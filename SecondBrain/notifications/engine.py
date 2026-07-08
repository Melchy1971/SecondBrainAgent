from datetime import datetime, timezone
from uuid import uuid4


class NotificationEngine:
    def __init__(self, store):
        self.store = store

    def send(self, title: str, body: str, channel: str = "desktop", priority: str = "info") -> dict:
        item = {
            "id": str(uuid4()),
            "title": title,
            "body": body,
            "channel": channel,
            "priority": priority,
            "status": "queued",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        return self.store.append("notifications", item)

    def list(self, limit: int = 50) -> list[dict]:
        return self.store.load("notifications", [])[-limit:]
