"""P3 v20.2 - Conversation Timeline."""

from dataclasses import dataclass, field
from time import time


@dataclass
class TimelineEvent:
    event_id: str
    text: str
    created_at: float = field(default_factory=time)


class ConversationTimeline:
    def __init__(self):
        self._events: list[TimelineEvent] = []

    def add(self, event: TimelineEvent):
        self._events.append(event)

    def list(self):
        return sorted(self._events, key=lambda x: x.created_at)
