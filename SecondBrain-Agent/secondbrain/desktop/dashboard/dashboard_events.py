from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class DashboardEventType(str, Enum):
    WIDGET_REGISTERED = "WIDGET_REGISTERED"
    WIDGET_REFRESHED = "WIDGET_REFRESHED"
    WIDGET_FAILED = "WIDGET_FAILED"
    DASHBOARD_LOADED = "DASHBOARD_LOADED"
    DASHBOARD_SAVED = "DASHBOARD_SAVED"


@dataclass(slots=True)
class DashboardEvent:
    event_type: DashboardEventType
    widget_id: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class DashboardEventLog:
    def __init__(self) -> None:
        self._events: list[DashboardEvent] = []

    def emit(self, event_type: DashboardEventType, *, widget_id: str | None = None, **payload: Any) -> DashboardEvent:
        event = DashboardEvent(event_type=event_type, widget_id=widget_id, payload=payload)
        self._events.append(event)
        return event

    def all(self) -> list[DashboardEvent]:
        return list(self._events)

    def clear(self) -> None:
        self._events.clear()
