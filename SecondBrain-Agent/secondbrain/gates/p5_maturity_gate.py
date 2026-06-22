"""P5 v23.2 - GUI Maturity Gate."""

class P5MaturityGate:
    REQUIRED = [
        "chat_stream",
        "dock_layout",
        "agent_live_console",
        "citation_viewer",
        "memory_graph_view",
        "connector_management",
        "persistent_settings",
    ]

    def evaluate(self, capabilities: dict[str, bool]):
        checks = {k: capabilities.get(k, False) for k in self.REQUIRED}
        return {
            "status": "PASS" if all(checks.values()) else "FAIL",
            "checks": checks,
        }
