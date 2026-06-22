from secondbrain.connectors.connector_registry import ConnectorRegistry


def run_connector_status():
    registry = ConnectorRegistry()
    return {
        "status": "PASS",
        "registered_connectors": registry.list(),
    }
