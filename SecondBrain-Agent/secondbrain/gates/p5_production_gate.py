"""P5 v23.1 - GUI Production Gate."""

class P5ProductionGate:
    REQUIRED = [
        "chat_view",
        "rag_explorer",
        "memory_explorer",
        "connector_center",
        "agent_runs_dashboard",
        "approval_inbox",
        "system_monitor",
        "settings_center",
        "production_dashboard",
        "notification_center",
        "widget_framework",
    ]

    def evaluate(self, capabilities: dict[str, bool]):
        checks = {k: capabilities.get(k, False) for k in self.REQUIRED}
        return {
            "status": "PASS" if all(checks.values()) else "FAIL",
            "checks": checks,
        }
