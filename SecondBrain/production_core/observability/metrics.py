from datetime import datetime, timezone


class MetricsCollector:
    def __init__(self, store):
        self.store = store

    def snapshot(self) -> dict:
        metrics = {
            "runtime_status": self.store.load("runtime_state", {"status": "stopped"}).get("status"),
            "audit_events": len(self.store.load("audit_log", [])),
            "approval_requests": len(self.store.load("approval_requests", [])),
            "watchdog_scans": len(self.store.load("watchdog_scans", [])),
            "backups": len(self.store.load("backups", [])),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.store.append("metrics", metrics)
        return metrics

    def history(self) -> list[dict]:
        return self.store.load("metrics", [])
