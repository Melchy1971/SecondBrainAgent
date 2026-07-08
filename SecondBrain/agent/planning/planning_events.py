from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable


@dataclass
class PlanningEvent:
    event_type: str
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class PlanningEventBus:
    def __init__(self) -> None:
        self.events: list[PlanningEvent] = []
        self.subscribers: list[Callable[[PlanningEvent], None]] = []

    def publish(self, event_type: str, payload: dict[str, Any] | None = None) -> PlanningEvent:
        event = PlanningEvent(event_type=event_type, payload=payload or {})
        self.events.append(event)
        for subscriber in list(self.subscribers):
            subscriber(event)
        return event

    def subscribe(self, callback: Callable[[PlanningEvent], None]) -> None:
        self.subscribers.append(callback)
