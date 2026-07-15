"""Scalable load, scaling and endurance profiles on top of the existing perf
harness (v30.98 delta).

The benchmark harness, performance history and regression gate already exist
(``secondbrain.perf.harness`` / ``history`` / ``regression``). This module adds
what they lack: reproducible load PROFILES, deterministic synthetic data
generators (never production data), resource limits with controlled abort,
checkpointed partial reports, baseline comparison (reusing ``perf.regression``)
and a bottleneck classifier feeding a ``load-gate`` verdict.

Pure standard library so profiles and the gate are deterministic and testable
without the full runtime; the actual large-scale execution runs against the
real system on the target machine.
"""

from __future__ import annotations

import json
import random
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Mapping, Sequence

from secondbrain.perf.regression import compare_runs  # reuse, do not rebuild

__all__ = [
    "LoadProfile", "PROFILES", "BOTTLENECK_CATEGORIES", "deterministic_dataset",
    "percentiles", "classify_bottleneck", "LoadRun", "run_load_gate",
    "PASS", "CONDITIONAL_PASS", "BLOCKED",
]

PASS = "PASS"
CONDITIONAL_PASS = "CONDITIONAL_PASS"
BLOCKED = "BLOCKED"
SCHEMA = "secondbrain.load_gate.v30_98"

_CONTENT_KEYS = frozenset({"text", "content", "body", "snippet", "document", "raw", "payload"})


def _scrub(data):
    """Drop content-bearing keys so no document text enters a report."""
    return {k: v for k, v in data.items() if k not in _CONTENT_KEYS}

BOTTLENECK_CATEGORIES = (
    "cpu", "memory", "disk", "database", "network", "provider",
    "lock_contention", "queue", "gui", "parser", "embedding",
)

# Default p95 ceilings (ms) and error-rate ceiling for the gate.
DEFAULT_LIMITS = {
    "vector_search_p95_ms": 250.0,
    "hybrid_search_p95_ms": 400.0,
    "gui_response_p95_ms": 800.0,
    "search_error_rate": 0.01,
    "queue_growth_ratio": 1.0,   # sustained arrivals must not exceed drain
}


@dataclass(frozen=True)
class LoadProfile:
    name: str
    documents: int
    chunks: int
    emails: int
    parallel_jobs: int
    parallel_searches: int
    file_bytes: int
    endurance_minutes: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name, "documents": self.documents, "chunks": self.chunks,
            "emails": self.emails, "parallel_jobs": self.parallel_jobs,
            "parallel_searches": self.parallel_searches, "file_bytes": self.file_bytes,
            "endurance_minutes": self.endurance_minutes,
        }


PROFILES: dict[str, LoadProfile] = {
    "small": LoadProfile("small", documents=10_000, chunks=100_000, emails=0,
                         parallel_jobs=5, parallel_searches=0, file_bytes=0, endurance_minutes=0),
    "medium": LoadProfile("medium", documents=100_000, chunks=1_000_000, emails=100_000,
                          parallel_jobs=10, parallel_searches=0, file_bytes=0, endurance_minutes=0),
    "large": LoadProfile("large", documents=0, chunks=0, emails=0,
                         parallel_jobs=0, parallel_searches=100, file_bytes=50 * 1024**3,
                         endurance_minutes=180),
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def deterministic_dataset(profile: LoadProfile, *, seed: int = 1337, limit: int = 1000) -> list[dict[str, Any]]:
    """Generate synthetic, reproducible records for a profile. The same
    (profile, seed) always yields identical output; records are explicitly
    marked synthetic so no production data can enter a load run."""
    rng = random.Random(f"{profile.name}:{seed}")
    n = min(limit, max(profile.documents, profile.chunks, profile.parallel_searches, 1))
    out: list[dict[str, Any]] = []
    for i in range(n):
        out.append({
            "id": f"synthetic-{profile.name}-{i}",
            "synthetic": True,               # never production data
            "token_count": rng.randint(50, 400),
            "vector_seed": rng.random(),
            "kind": rng.choice(("doc", "email", "chunk")),
        })
    return out


def percentiles(samples: Sequence[float]) -> dict[str, float]:
    if not samples:
        return {"p50": 0.0, "p95": 0.0, "p99": 0.0}
    ordered = sorted(samples)

    def q(p: float) -> float:
        idx = min(len(ordered) - 1, int(round(p * (len(ordered) - 1))))
        return round(ordered[idx], 3)

    return {"p50": q(0.50), "p95": q(0.95), "p99": q(0.99)}


def classify_bottleneck(saturation: Mapping[str, float]) -> str:
    """Return the dominant bottleneck category. ``saturation`` maps a subset of
    BOTTLENECK_CATEGORIES to a 0..1 utilization; the highest wins. Unknown keys
    are ignored; no signal -> 'cpu' as the conservative default."""
    known = {k: float(v) for k, v in saturation.items() if k in BOTTLENECK_CATEGORIES}
    if not known:
        return "cpu"
    return max(known.items(), key=lambda kv: kv[1])[0]


@dataclass
class LoadRun:
    """A checkpointed load run. Metrics accumulate; ``abort_if`` allows a
    controlled early stop; ``checkpoints`` retain partial progress so a stopped
    run still yields a usable partial report."""

    profile: LoadProfile
    limits: dict[str, float] = field(default_factory=lambda: dict(DEFAULT_LIMITS))
    checkpoints: list[dict[str, Any]] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    aborted: bool = False
    abort_reason: str = ""

    def checkpoint(self, step: str, data: Mapping[str, Any]) -> None:
        self.checkpoints.append({"step": step, "at": _now(), **_scrub(data)})

    def run(self, steps: Sequence[tuple[str, Callable[[], dict[str, Any]]]], *,
            abort_if: Callable[[dict[str, Any]], str | None] | None = None) -> dict[str, Any]:
        for name, step in steps:
            result = step()
            self.checkpoint(name, result)
            self.metrics[name] = _scrub(result)
            if abort_if is not None:
                reason = abort_if(result)
                if reason:
                    self.aborted = True
                    self.abort_reason = reason
                    break
        return self.partial_report()

    def partial_report(self) -> dict[str, Any]:
        # report carries only metrics/metadata, never document content
        return {
            "schema": "secondbrain.load_run.v30_98",
            "profile": self.profile.to_dict(),
            "aborted": self.aborted,
            "abort_reason": self.abort_reason,
            "completed_steps": [c["step"] for c in self.checkpoints],
            "metrics": self.metrics,
            "at": _now(),
        }


def run_load_gate(current: Mapping[str, Any], *, baseline: Mapping[str, Any] | None = None,
                  limits: Mapping[str, float] | None = None) -> dict[str, Any]:
    """Grade a load run. Hard BLOCKED conditions (data loss, OOM, deadlock,
    double execution, search error rate over limit, p95 over limit, GUI freeze,
    unbounded queue growth, DB corruption) fail the gate; soft warnings degrade
    to CONDITIONAL_PASS."""
    lim = {**DEFAULT_LIMITS, **(limits or {})}
    blockers: list[str] = []
    warnings: list[str] = []

    flags = current.get("flags", {})
    for hard in ("data_loss", "oom", "deadlock", "double_execution", "gui_freeze", "db_corruption"):
        if flags.get(hard):
            blockers.append(hard)

    err = float(current.get("search_error_rate", 0.0))
    if err > lim["search_error_rate"]:
        blockers.append("search_error_rate")

    for metric in ("vector_search_p95_ms", "hybrid_search_p95_ms", "gui_response_p95_ms"):
        value = current.get(metric)
        if value is not None and float(value) > lim[metric]:
            blockers.append(metric)

    if float(current.get("queue_growth_ratio", 0.0)) > lim["queue_growth_ratio"]:
        blockers.append("queue_growth")

    if flags.get("provider_throttled"):
        warnings.append("provider_limiting")
    if flags.get("perf_warning"):
        warnings.append("performance_warning")

    regressions: list[dict[str, Any]] = []
    if baseline is not None:
        base_cases = baseline.get("cases", [])
        cur_cases = current.get("cases", [])
        if base_cases and cur_cases:
            comparison = compare_runs(cur_cases, base_cases)
            regressions = [r.to_dict() for r in comparison if r.regressed]
            if regressions:
                warnings.append("baseline_regression")

    status = BLOCKED if blockers else (CONDITIONAL_PASS if warnings else PASS)
    bottleneck = classify_bottleneck(current.get("saturation", {}))
    return {
        "schema": SCHEMA,
        "at": _now(),
        "status": status,
        "blockers": blockers,
        "warnings": warnings,
        "bottleneck": bottleneck,
        "regressions": regressions,
        "limits": lim,
    }


def main(argv: list[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Load profile runner (framework)")
    parser.add_argument("--profile", choices=sorted(PROFILES), default="small")
    args = parser.parse_args(argv)
    profile = PROFILES[args.profile]
    data = deterministic_dataset(profile, limit=100)
    print(json.dumps({"profile": profile.to_dict(), "sample_records": len(data),
                      "reproducible": True}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
