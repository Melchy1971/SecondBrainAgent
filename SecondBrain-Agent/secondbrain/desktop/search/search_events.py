from __future__ import annotations

SEARCH_STARTED = "SEARCH_STARTED"
SEARCH_COMPLETED = "SEARCH_COMPLETED"
SEARCH_FAILED = "SEARCH_FAILED"
SEARCH_FILTER_CHANGED = "SEARCH_FILTER_CHANGED"
SEARCH_HISTORY_UPDATED = "SEARCH_HISTORY_UPDATED"


class SearchEventBus:
    def __init__(self) -> None:
        self.events: list[dict] = []

    def emit(self, event_type: str, **payload) -> None:
        self.events.append({"type": event_type, "payload": payload})

    def by_type(self, event_type: str) -> list[dict]:
        return [event for event in self.events if event["type"] == event_type]
