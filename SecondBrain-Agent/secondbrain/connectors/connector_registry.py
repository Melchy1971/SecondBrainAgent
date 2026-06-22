"""P4 v22.0 - Connector Registry."""

class ConnectorRegistry:
    def __init__(self):
        self._connectors = {}

    def register(self, name: str, connector):
        self._connectors[name] = connector

    def get(self, name: str):
        return self._connectors.get(name)

    def list(self):
        return sorted(self._connectors.keys())
