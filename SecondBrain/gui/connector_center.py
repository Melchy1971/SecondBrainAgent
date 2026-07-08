"""P5 v23.0 - Connector Center."""

class ConnectorCenter:
    def render(self, connectors: list[str]):
        return {
            "connectors": sorted(connectors),
            "count": len(connectors),
        }
