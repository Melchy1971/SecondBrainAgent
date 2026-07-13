"""Health Timeline: Komponenten-Status über die Zeit, aktueller Gesamtzustand."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS_ORDER = {"ok": 0, "degraded": 1, "blocked": 2, "failed": 2}
VALID_STATUSES = ("ok", "degraded", "blocked", "failed")


class HealthTimeline:
    def __init__(self, project_root: str | Path = "."):
        self.project_root = Path(project_root)
        self.path = self.project_root / "runtime" / "observability" / "health_timeline.jsonl"

    def record(self, component: str, status: str, detail: str = "",
               *, correlation_id: str = "") -> dict[str, Any]:
        if status not in VALID_STATUSES:
            status = "degraded"
        entry: dict[str, Any] = {
            "schema": "secondbrain.observability.health.v1",
            "ts": datetime.now(timezone.utc).isoformat(),
            "component": component,
            "status": status,
        }
        if detail:
            entry["detail"] = detail[:500]
        if correlation_id:
            entry["correlation_id"] = correlation_id
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return entry

    def timeline(self, limit: int = 200, component: str | None = None) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        entries: list[dict[str, Any]] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if component and entry.get("component") != component:
                continue
            entries.append(entry)
        return entries[-limit:]

    def current(self) -> dict[str, Any]:
        """Letzter Status je Komponente + Gesamtzustand (schlechtester Einzelstatus)."""
        latest: dict[str, dict[str, Any]] = {}
        for entry in self.timeline(limit=2000):
            latest[entry["component"]] = entry
        overall = "ok"
        for entry in latest.values():
            if STATUS_ORDER.get(entry["status"], 1) > STATUS_ORDER.get(overall, 0):
                overall = entry["status"]
        return {
            "schema": "secondbrain.observability.health_current.v1",
            "overall": overall if latest else "unknown",
            "components": {name: {"status": e["status"], "ts": e["ts"], "detail": e.get("detail", "")}
                           for name, e in sorted(latest.items())},
        }
