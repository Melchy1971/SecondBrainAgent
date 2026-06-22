"""P5 v23.2 - Connector Management UI."""

class ConnectorManagement:
    def render(self, connectors: list[dict]):
        return {
            "count": len(connectors),
            "connectors": connectors,
        }
