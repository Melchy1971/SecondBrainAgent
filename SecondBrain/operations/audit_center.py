"""P8 v26.1 - Audit Center."""

from time import time


class AuditCenter:
    def __init__(self):
        self._events = []

    def record(self, category: str, action: str):
        self._events.append({
            "category": category,
            "action": action,
            "timestamp": time(),
        })

    def list(self):
        return list(self._events)
