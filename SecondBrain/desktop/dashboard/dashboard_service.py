from __future__ import annotations

from pathlib import Path
from typing import Mapping, Any

from .dashboard_events import DashboardEventLog, DashboardEventType
from .dashboard_persistence import DashboardPersistence
from .dashboard_state import DashboardState
from .refresh_scheduler import RefreshScheduler
from .widget_base import DashboardWidget, WidgetProvider
from .widget_manager import WidgetManager
from .widget_registry import WidgetRegistry


DEFAULT_WIDGETS = (
    ("recent_imports", "Recent Imports"),
    ("running_jobs", "Running Jobs"),
    ("connector_health", "Connector Health"),
    ("rag_status", "RAG Status"),
    ("system_health", "System Health"),
    ("storage_usage", "Storage Usage"),
    ("recent_errors", "Recent Errors"),
    ("workspace_summary", "Workspace Summary"),
)


class DashboardService:
    def __init__(self, config_root: str | Path, providers: Mapping[str, WidgetProvider] | None = None) -> None:
        self.events = DashboardEventLog()
        self.state = DashboardState()
        self.persistence = DashboardPersistence(Path(config_root) / "dashboard")
        self.registry = WidgetRegistry(self.events)
        self.manager = WidgetManager(self.registry, self.events)
        self.scheduler = RefreshScheduler(self.manager)
        self.providers = dict(providers or {})

    def bootstrap_defaults(self) -> list[DashboardWidget]:
        registered: list[DashboardWidget] = []
        for widget_id, title in DEFAULT_WIDGETS:
            if widget_id in self.registry.ids():
                continue
            widget = DashboardWidget(widget_id=widget_id, title=title)
            registered.append(self.registry.register(widget, self.providers.get(widget_id)))
            self.state.enable_widget(widget_id)
        return registered

    def load(self) -> DashboardState:
        self.state = self.persistence.load_state()
        self.events.emit(DashboardEventType.DASHBOARD_LOADED, layout=self.state.active_layout)
        return self.state

    def save(self) -> None:
        self.state.touch()
        self.persistence.save_state(self.state)
        self.persistence.save_widgets(self.registry.all())
        self.events.emit(DashboardEventType.DASHBOARD_SAVED, layout=self.state.active_layout)

    def refresh(self, widget_id: str) -> DashboardWidget:
        widget = self.manager.refresh(widget_id, self.state.selected_workspace)
        self.state.touch()
        return widget

    def refresh_all(self) -> list[DashboardWidget]:
        widgets = self.manager.refresh_all(self.state.selected_workspace)
        self.state.touch()
        return widgets

    def snapshot(self) -> dict[str, Any]:
        return {
            "layout": self.state.active_layout,
            "workspace": self.state.selected_workspace,
            "widgets": [
                {
                    "widget_id": widget.widget_id,
                    "title": widget.title,
                    "enabled": widget.enabled,
                    "status": widget.status.value,
                    "error": widget.error,
                    "data": widget.data,
                }
                for widget in self.registry.all()
            ],
        }
