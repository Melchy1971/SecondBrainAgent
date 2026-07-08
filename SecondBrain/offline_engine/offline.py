from datetime import datetime, timezone
from uuid import uuid4


class OfflineEngine:
    def __init__(self, store):
        self.store = store

    def capture(self, device_id: str, kind: str, payload: dict) -> dict:
        item = {
            "id": str(uuid4()),
            "device_id": device_id,
            "kind": kind,
            "payload": payload,
            "status": "queued",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        return self.store.append("offline_queue", item)

    def queue(self) -> list[dict]:
        return self.store.load("offline_queue", [])

    def replay(self) -> list[dict]:
        queued = self.queue()
        replayed = [{**item, "status": "replayed", "replayed_at": datetime.now(timezone.utc).isoformat()} for item in queued]
        history = self.store.load("offline_history", [])
        history.extend(replayed)
        self.store.save("offline_history", history)
        self.store.save("offline_queue", [])
        return replayed
