"""Activity feed model (recent events, filterable)."""

from __future__ import annotations

from datetime import datetime, timezone


class ActivityFeedModel:
    def __init__(self, capacity: int = 200) -> None:
        self.capacity = capacity
        self._events: list[dict] = []

    def add(self, kind: str, text: str, *, severity: str = "info") -> dict:
        event = {"timestamp": datetime.now(timezone.utc).isoformat(), "kind": kind,
                 "text": text, "severity": severity}
        self._events.append(event)
        if len(self._events) > self.capacity:
            self._events = self._events[-self.capacity:]
        return event

    def recent(self, limit: int = 20) -> list[dict]:
        return list(reversed(self._events[-limit:]))

    def by_kind(self, kind: str) -> list[dict]:
        return [e for e in self._events if e["kind"] == kind]

    def by_severity(self, severity: str) -> list[dict]:
        return [e for e in self._events if e["severity"] == severity]
