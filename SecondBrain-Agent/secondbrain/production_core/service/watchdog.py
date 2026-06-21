from datetime import datetime, timezone
from uuid import uuid4


class Watchdog:
    def __init__(self, store):
        self.store = store

    def heartbeat(self, component: str = "runtime") -> dict:
        state = self.store.load("heartbeats", {})
        state[component] = datetime.now(timezone.utc).isoformat()
        self.store.save("heartbeats", state)
        return {"component": component, "heartbeat": state[component]}

    def scan(self) -> dict:
        heartbeats = self.store.load("heartbeats", {})
        runtime = self.store.load("runtime_state", {"status": "stopped"})
        issues = []
        if runtime.get("status") != "running":
            issues.append({"component": "runtime", "issue": "not_running", "severity": "critical"})
        if not heartbeats:
            issues.append({"component": "watchdog", "issue": "no_heartbeats", "severity": "warning"})
        scan = {
            "id": str(uuid4()),
            "status": "healthy" if not issues else "degraded",
            "issues": issues,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.store.append("watchdog_scans", scan)
        return scan

    def recover(self) -> dict:
        scan = self.scan()
        actions = []
        runtime = self.store.load("runtime_state", {"status": "stopped"})
        if runtime.get("status") != "running":
            runtime["status"] = "running"
            runtime["recovered_at"] = datetime.now(timezone.utc).isoformat()
            self.store.save("runtime_state", runtime)
            actions.append("restart_runtime")
        return {"scan": scan, "actions": actions, "status": "recovered" if actions else "no_action"}
