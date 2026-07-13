from uuid import uuid4
from .models import MobileCommand
from .store import JsonStore


class OfflineQueue:
    def __init__(self, store: JsonStore):
        self.store = store

    def items(self) -> list[dict]:
        return self.store.load("offline_queue", [])

    def enqueue(self, device_id: str, command: str, payload: dict) -> dict:
        item = MobileCommand(str(uuid4()), device_id, command, payload).to_dict()
        queue = self.items()
        queue.append(item)
        self.store.save("offline_queue", queue)
        return item

    def drain(self, limit: int = 10) -> list[dict]:
        queue = self.items()
        ready = queue[:limit]
        remaining = queue[limit:]
        drained = [{**item, "status": "drained"} for item in ready]
        self.store.save("offline_queue", remaining)
        history = self.store.load("offline_history", [])
        history.extend(drained)
        self.store.save("offline_history", history)
        return drained
