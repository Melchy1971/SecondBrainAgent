from __future__ import annotations

from datetime import datetime, timezone

from .widget_base import DashboardWidget
from .widget_manager import WidgetManager


class RefreshScheduler:
    def __init__(self, manager: WidgetManager) -> None:
        self.manager = manager

    def due_widgets(self, widgets: list[DashboardWidget], now: datetime | None = None) -> list[DashboardWidget]:
        current = now or datetime.now(timezone.utc)
        due: list[DashboardWidget] = []
        for widget in widgets:
            if not widget.enabled:
                continue
            if widget.last_refresh is None:
                due.append(widget)
                continue
            elapsed = (current - widget.last_refresh).total_seconds()
            if elapsed >= widget.refresh_interval:
                due.append(widget)
        return due

    def refresh_due(self, widgets: list[DashboardWidget], workspace_id: str = "default", now: datetime | None = None) -> list[DashboardWidget]:
        return [self.manager.refresh(widget.widget_id, workspace_id) for widget in self.due_widgets(widgets, now=now)]
