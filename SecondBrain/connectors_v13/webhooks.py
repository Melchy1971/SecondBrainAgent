from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4


class WebhookInbox:
    def __init__(self, store):
        self.store = store

    def receive(self, connector_id: str, event_type: str, payload: dict) -> dict:
        item = {
            "id": str(uuid4()),
            "connector_id": connector_id,
            "event_type": event_type,
            "payload": payload,
            "status": "received",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        return self.store.append("webhooks", item)

    def list_items(self, limit: int = 50) -> list[dict]:
        return self.store.load("webhooks", [])[-limit:]

    def list(self, limit: int = 50) -> list[dict]:
        # Backward-compatible public API. The annotations are postponed so this
        # method name no longer shadows the built-in list during class creation.
        return self.list_items(limit)

    def drain(self) -> list[dict]:
        items = self.store.load("webhooks", [])
        drained = [{**i, "status": "processed", "processed_at": datetime.now(timezone.utc).isoformat()} for i in items]
        history = self.store.load("webhook_history", [])
        history.extend(drained)
        self.store.save("webhook_history", history)
        self.store.save("webhooks", [])
        return drained
