"""v27.0 - Observability Foundation."""

from time import time


class ObservabilityCenter:
    def __init__(self):
        self._events = []

    def emit(self, level: str, message: str):
        self._events.append({
            "timestamp": time(),
            "level": level,
            "message": message,
        })

    def events(self):
        return list(self._events)
