"""P8 v26.1 - Monitoring & Alerting."""

class MonitoringService:
    def health(self, components: dict):
        failed = [k for k, v in components.items() if not v]
        return {
            "status": "PASS" if not failed else "FAIL",
            "failed_components": failed,
        }
