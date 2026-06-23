from __future__ import annotations

from .dashboard_events import DashboardEventLog, DashboardEventType
from .widget_base import DashboardWidget
from .widget_registry import WidgetRegistry


class WidgetManager:
    def __init__(self, registry: WidgetRegistry, events: DashboardEventLog | None = None) -> None:
        self.registry = registry
        self.events = events or DashboardEventLog()

    def refresh(self, widget_id: str, workspace_id: str = "default") -> DashboardWidget:
        widget = self.registry.get(widget_id)
        if not widget.enabled:
            widget.mark_disabled()
            return widget
        provider = self.registry.provider_for(widget_id)
        if provider is None:
            widget.mark_ready({})
            self.events.emit(DashboardEventType.WIDGET_REFRESHED, widget_id=widget_id, empty=True)
            return widget
        widget.mark_refreshing()
        try:
            widget.mark_ready(provider(workspace_id))
            self.events.emit(DashboardEventType.WIDGET_REFRESHED, widget_id=widget_id)
        except Exception as exc:  # deterministic failure isolation at widget boundary
            widget.mark_failed(str(exc))
            self.events.emit(DashboardEventType.WIDGET_FAILED, widget_id=widget_id, error=str(exc))
        return widget

    def refresh_all(self, workspace_id: str = "default") -> list[DashboardWidget]:
        return [self.refresh(widget.widget_id, workspace_id) for widget in self.registry.enabled()]
