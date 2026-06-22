"""P4 v22.2 - Connector Event Bus."""

class ConnectorEventBus:
    def __init__(self):
        self._events = []

    def publish(self, event_type: str, payload: dict):
        self._events.append({"type": event_type, "payload": payload})

    def list(self):
        return list(self._events)
