"""P3 v20.0 - Episodic Memory Foundation."""

from __future__ import annotations
from dataclasses import dataclass, field
from time import time


@dataclass
class EpisodicMemory:
    event_id: str
    summary: str
    tags: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=time)


class EpisodicMemoryStore:
    def __init__(self):
        self._events: dict[str, EpisodicMemory] = {}

    def add(self, event: EpisodicMemory) -> None:
        self._events[event.event_id] = event

    def list(self) -> list[EpisodicMemory]:
        return list(self._events.values())
