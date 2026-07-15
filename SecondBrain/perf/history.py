"""Append-only run history (JSONL) and trend extraction."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

__all__ = ["append_run", "load_history", "latest_baseline", "trend"]


def append_run(path: str | Path, run: dict[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(run, ensure_ascii=False) + "\n")


def load_history(path: str | Path) -> list[dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        return []
    runs: list[dict[str, Any]] = []
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            runs.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return runs


def latest_baseline(history: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Most recent prior run used as the regression baseline (or None)."""

    return history[-1] if history else None


def trend(history: list[dict[str, Any]], component: str, case: str, *, metric: str = "per_iter_ms") -> list[dict[str, Any]]:
    series: list[dict[str, Any]] = []
    for run in history:
        for r in run.get("results", []):
            if r.get("component") == component and r.get("case") == case and r.get("status") == "ok":
                value = r.get("metrics", {}).get(metric)
                if value is not None:
                    series.append({"timestamp": run.get("timestamp"), "value": value})
    return series
