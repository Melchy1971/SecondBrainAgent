from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Callable, DefaultDict


class EventType(StrEnum):
    DOCUMENT_IMPORTED = "DOCUMENT_IMPORTED"
    DOCUMENT_INDEXED = "DOCUMENT_INDEXED"
    CONNECTOR_SYNCED = "CONNECTOR_SYNCED"
    JOB_STARTED = "JOB_STARTED"
    JOB_FINISHED = "JOB_FINISHED"
    ERROR_OCCURRED = "ERROR_OCCURRED"


@dataclass(frozen=True, slots=True)
class DesktopEvent:
    type: EventType
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


EventHandler = Callable[[DesktopEvent], None]


class EventBus:
    def __init__(self) -> None:
        self._handlers: DefaultDict[EventType, list[EventHandler]] = defaultdict(list)
        self._history: list[DesktopEvent] = []

    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        if handler not in self._handlers[event_type]:
            self._handlers[event_type].append(handler)

    def unsubscribe(self, event_type: EventType, handler: EventHandler) -> None:
        if handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)

    def publish(self, event: DesktopEvent) -> None:
        self._history.append(event)
        for handler in list(self._handlers[event.type]):
            handler(event)

    def history(self, limit: int | None = None) -> list[DesktopEvent]:
        if limit is None:
            return list(self._history)
        return list(self._history[-limit:])
