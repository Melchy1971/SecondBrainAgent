"""P4 v22.1 - Connector Scheduler."""

class ConnectorScheduler:
    def build_schedule(self, connectors: list[str]):
        return [
            {"connector": connector, "enabled": True}
            for connector in connectors
        ]
