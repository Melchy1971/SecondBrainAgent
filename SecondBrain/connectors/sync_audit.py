"""P4 v22.1 - Sync Audit."""

from time import time


class SyncAudit:
    def __init__(self):
        self._events = []

    def record(self, connector: str, status: str, items: int = 0):
        self._events.append({
            "connector": connector,
            "status": status,
            "items": items,
            "timestamp": time(),
        })

    def list(self):
        return list(self._events)
