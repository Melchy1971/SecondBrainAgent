"""Regression detection against a baseline run.

A component/case regresses when its primary metric (per-iteration time by
default) exceeds the baseline by more than the threshold (default 10 %). The
gate fails if any ``ok`` case regresses.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

__all__ = ["DEFAULT_THRESHOLD", "PRIMARY_METRIC", "Regression", "compare_runs", "gate"]

DEFAULT_THRESHOLD = 0.10
PRIMARY_METRIC = "per_iter_ms"


@dataclass
class Regression:
    key: str
    metric: str
    baseline: float
    current: float
    delta_pct: float
    regressed: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def compare_runs(
    current_results: Sequence[Mapping[str, Any]],
    baseline_results: Sequence[Mapping[str, Any]],
    *,
    threshold: float = DEFAULT_THRESHOLD,
    metric: str = PRIMARY_METRIC,
) -> list[Regression]:
    baseline = {
        (r.get("component"), r.get("case")): r
        for r in baseline_results
        if r.get("status") == "ok"
    }
    out: list[Regression] = []
    for r in current_results:
        if r.get("status") != "ok":
            continue
        key = (r.get("component"), r.get("case"))
        base = baseline.get(key)
        if base is None:
            continue
        bv = _num(base.get("metrics", {}).get(metric))
        cv = _num(r.get("metrics", {}).get(metric))
        if bv <= 0:
            continue
        delta = (cv - bv) / bv
        out.append(
            Regression(
                key=f"{key[0]}/{key[1]}",
                metric=metric,
                baseline=round(bv, 4),
                current=round(cv, 4),
                delta_pct=round(delta * 100.0, 2),
                regressed=delta > threshold,
            )
        )
    return out


def gate(regressions: Sequence[Regression], *, threshold: float = DEFAULT_THRESHOLD) -> dict[str, Any]:
    regressed = [r for r in regressions if r.regressed]
    return {
        "status": "FAIL" if regressed else "PASS",
        "threshold_pct": round(threshold * 100.0, 2),
        "compared": len(regressions),
        "regressions": [r.to_dict() for r in regressed],
    }


def _num(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0
