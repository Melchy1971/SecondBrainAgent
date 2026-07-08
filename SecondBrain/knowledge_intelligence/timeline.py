from datetime import datetime, timezone
from uuid import uuid4


class TimelineAnalytics:
    def __init__(self, store):
        self.store = store

    def add_event(self, title: str, kind: str = "note", entity: str | None = None, timestamp: str | None = None) -> dict:
        event = {
            "id": str(uuid4()),
            "title": title,
            "kind": kind,
            "entity": entity,
            "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
        }
        return self.store.append("timeline", event)

    def timeline(self, entity: str | None = None) -> list[dict]:
        events = self.store.load("timeline", [])
        if entity:
            return [e for e in events if (e.get("entity") or "").lower() == entity.lower()]
        return sorted(events, key=lambda e: e["timestamp"])
