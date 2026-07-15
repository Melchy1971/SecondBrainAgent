"""Health snapshot history (JSONL timeline) and export helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

__all__ = ["append_snapshot", "load_history", "timeline", "trend", "export_snapshot"]


def append_snapshot(path: str | Path, snapshot: dict[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(snapshot, ensure_ascii=False) + "\n")


def load_history(path: str | Path) -> list[dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        return []
    out: list[dict[str, Any]] = []
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def timeline(history: list[dict[str, Any]], *, limit: int = 40) -> list[dict[str, Any]]:
    """Recent overall states for the timeline strip (oldest -> newest)."""

    recent = history[-max(1, int(limit)):]
    return [{"timestamp": s.get("timestamp"), "overall": s.get("overall"), "ampel": s.get("ampel")} for s in recent]


def trend(history: list[dict[str, Any]], component: str, metric: str = "percent") -> list[dict[str, Any]]:
    series: list[dict[str, Any]] = []
    for snap in history:
        for c in snap.get("checks", []):
            if c.get("component") == component:
                value = c.get("metrics", {}).get(metric)
                if value is not None:
                    series.append({"timestamp": snap.get("timestamp"), "value": value})
    return series


def export_snapshot(snapshot: dict[str, Any]) -> str:
    """JSON export string of a single snapshot (secrets already excluded upstream)."""

    return json.dumps(snapshot, ensure_ascii=False, indent=2)
