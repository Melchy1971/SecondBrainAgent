from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from .dashboard_state import DashboardState
from .widget_base import DashboardWidget, WidgetStatus


def _dt(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _parse_dt(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


class DashboardPersistence:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def save_state(self, state: DashboardState) -> Path:
        payload = asdict(state)
        payload["last_update"] = _dt(state.last_update)
        path = self.root / "preferences.json"
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return path

    def load_state(self) -> DashboardState:
        path = self.root / "preferences.json"
        if not path.exists():
            return DashboardState()
        payload: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        payload["last_update"] = _parse_dt(payload.get("last_update"))
        return DashboardState(**payload)

    def save_widgets(self, widgets: list[DashboardWidget]) -> Path:
        payload = []
        for widget in widgets:
            item = asdict(widget)
            item["status"] = widget.status.value
            item["last_refresh"] = _dt(widget.last_refresh)
            payload.append(item)
        path = self.root / "widgets.json"
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return path

    def load_widgets(self) -> list[DashboardWidget]:
        path = self.root / "widgets.json"
        if not path.exists():
            return []
        payload = json.loads(path.read_text(encoding="utf-8"))
        widgets: list[DashboardWidget] = []
        for item in payload:
            item["status"] = WidgetStatus(item.get("status", WidgetStatus.IDLE.value))
            item["last_refresh"] = _parse_dt(item.get("last_refresh"))
            widgets.append(DashboardWidget(**item))
        return widgets
