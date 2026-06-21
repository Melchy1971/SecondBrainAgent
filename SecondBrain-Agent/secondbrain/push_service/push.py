from datetime import datetime, timezone
from uuid import uuid4


class PushService:
    def __init__(self, store):
        self.store = store

    def send(self, title: str, body: str, channel: str = "desktop", priority: str = "info", device_id: str | None = None) -> dict:
        msg = {
            "id": str(uuid4()),
            "title": title,
            "body": body,
            "channel": channel,
            "priority": priority,
            "device_id": device_id,
            "status": "queued",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        return self.store.append("push_outbox", msg)

    def outbox(self) -> list[dict]:
        return self.store.load("push_outbox", [])

    def deliver(self) -> list[dict]:
        outbox = self.outbox()
        delivered = [{**m, "status": "delivered", "delivered_at": datetime.now(timezone.utc).isoformat()} for m in outbox]
        history = self.store.load("push_history", [])
        history.extend(delivered)
        self.store.save("push_history", history)
        self.store.save("push_outbox", [])
        return delivered
