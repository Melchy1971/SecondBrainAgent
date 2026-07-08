from datetime import datetime, timezone
from .store import JsonStore


class MobileSyncProtocol:
    def __init__(self, store: JsonStore):
        self.store = store

    def status(self) -> dict:
        return {
            "last_sync": self.store.load("sync_state", {}).get("last_sync"),
            "pending_commands": len(self.store.load("offline_queue", [])),
            "pending_push": len(self.store.load("push_outbox", [])),
        }

    def sync(self, device_id: str) -> dict:
        state = {
            "device_id": device_id,
            "last_sync": datetime.now(timezone.utc).isoformat(),
            "protocol": "local-json-v1",
        }
        self.store.save("sync_state", state)
        return state
