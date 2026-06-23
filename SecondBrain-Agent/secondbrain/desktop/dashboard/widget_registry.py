from __future__ import annotations

from dataclasses import replace
from typing import Iterable

from .dashboard_events import DashboardEventLog, DashboardEventType
from .widget_base import DashboardWidget, WidgetProvider


class WidgetRegistryError(ValueError):
    pass


class WidgetRegistry:
    def __init__(self, events: DashboardEventLog | None = None) -> None:
        self._widgets: dict[str, DashboardWidget] = {}
        self._providers: dict[str, WidgetProvider] = {}
        self._events = events or DashboardEventLog()

    def register(self, widget: DashboardWidget, provider: WidgetProvider | None = None) -> DashboardWidget:
        if not widget.widget_id.strip():
            raise WidgetRegistryError("widget_id is required")
        if widget.widget_id in self._widgets:
            raise WidgetRegistryError(f"widget already registered: {widget.widget_id}")
        self._widgets[widget.widget_id] = replace(widget)
        if provider is not None:
            self._providers[widget.widget_id] = provider
        self._events.emit(DashboardEventType.WIDGET_REGISTERED, widget_id=widget.widget_id, title=widget.title)
        return self._widgets[widget.widget_id]

    def get(self, widget_id: str) -> DashboardWidget:
        try:
            return self._widgets[widget_id]
        except KeyError as exc:
            raise WidgetRegistryError(f"unknown widget: {widget_id}") from exc

    def provider_for(self, widget_id: str) -> WidgetProvider | None:
        return self._providers.get(widget_id)

    def all(self) -> list[DashboardWidget]:
        return list(self._widgets.values())

    def ids(self) -> list[str]:
        return list(self._widgets.keys())

    def enabled(self) -> Iterable[DashboardWidget]:
        return (widget for widget in self._widgets.values() if widget.enabled)
