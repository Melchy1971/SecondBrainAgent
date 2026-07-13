from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(slots=True)
class DashboardState:
    active_layout: str = "default"
    enabled_widgets: list[str] = field(default_factory=list)
    refresh_enabled: bool = True
    selected_workspace: str = "default"
    last_update: datetime | None = None

    def touch(self) -> None:
        self.last_update = datetime.now(timezone.utc)

    def enable_widget(self, widget_id: str) -> None:
        if widget_id not in self.enabled_widgets:
            self.enabled_widgets.append(widget_id)
            self.touch()

    def disable_widget(self, widget_id: str) -> None:
        self.enabled_widgets = [item for item in self.enabled_widgets if item != widget_id]
        self.touch()
