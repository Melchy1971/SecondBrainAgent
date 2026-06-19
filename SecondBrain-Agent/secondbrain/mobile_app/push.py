from uuid import uuid4
from datetime import datetime, timezone
from .store import JsonStore


class PushOutbox:
    def __init__(self, store: JsonStore):
        self.store = store

    def list(self) -> list[dict]:
        return self.store.load("push_outbox", [])

    def send(self, title: str, body: str, device_id: str | None = None, priority: str = "normal") -> dict:
        item = {
            "id": str(uuid4()),
            "device_id": device_id,
            "title": title,
            "body": body,
            "priority": priority,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "queued",
        }
        items = self.list()
        items.append(item)
        self.store.save("push_outbox", items)
        return item
