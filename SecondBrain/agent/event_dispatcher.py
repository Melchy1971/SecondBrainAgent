"""v30.3 - workflow event dispatcher."""

from __future__ import annotations

from dataclasses import dataclass
from time import time


@dataclass(frozen=True)
class AgentEvent:
    event_type: str
    payload: dict
    created_at: float = time()


class AgentEventDispatcher:
    def __init__(self):
        self._events: list[AgentEvent] = []

    def dispatch(self, event_type: str, payload: dict) -> AgentEvent:
        event = AgentEvent(event_type=event_type, payload=payload)
        self._events.append(event)
        return event

    def list(self) -> list[AgentEvent]:
        return list(self._events)
