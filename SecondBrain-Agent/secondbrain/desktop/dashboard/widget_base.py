from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Mapping


class WidgetStatus(str, Enum):
    IDLE = "idle"
    REFRESHING = "refreshing"
    READY = "ready"
    FAILED = "failed"
    DISABLED = "disabled"


@dataclass(slots=True)
class DashboardWidget:
    widget_id: str
    title: str
    enabled: bool = True
    refresh_interval: int = 60
    last_refresh: datetime | None = None
    status: WidgetStatus = WidgetStatus.IDLE
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    def mark_disabled(self) -> None:
        self.status = WidgetStatus.DISABLED

    def mark_refreshing(self) -> None:
        self.status = WidgetStatus.REFRESHING
        self.error = None

    def mark_ready(self, data: Mapping[str, Any] | None = None) -> None:
        self.status = WidgetStatus.READY
        self.data = dict(data or {})
        self.last_refresh = datetime.now(timezone.utc)
        self.error = None

    def mark_failed(self, error: str) -> None:
        self.status = WidgetStatus.FAILED
        self.error = error
        self.last_refresh = datetime.now(timezone.utc)


WidgetProvider = Callable[[str], Mapping[str, Any]]
