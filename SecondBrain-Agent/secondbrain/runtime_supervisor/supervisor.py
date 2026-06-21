from datetime import datetime, timezone
from uuid import uuid4


DEFAULT_SERVICES = [
    {"name": "event_bus", "dependencies": [], "critical": True},
    {"name": "tool_registry", "dependencies": ["event_bus"], "critical": True},
    {"name": "memory", "dependencies": ["event_bus"], "critical": True},
    {"name": "rag", "dependencies": ["memory"], "critical": False},
    {"name": "knowledge_graph", "dependencies": ["memory"], "critical": False},
    {"name": "swarm", "dependencies": ["tool_registry", "rag"], "critical": False},
    {"name": "learning", "dependencies": ["memory"], "critical": False},
    {"name": "digital_twin", "dependencies": ["learning"], "critical": False},
    {"name": "desktop", "dependencies": ["event_bus"], "critical": False},
    {"name": "mobile", "dependencies": ["event_bus"], "critical": False},
    {"name": "voice", "dependencies": ["event_bus"], "critical": False},
]


class RuntimeSupervisor:
    def __init__(self, store):
        self.store = store

    def services(self) -> list[dict]:
        configured = self.store.load("services", None)
        if configured is None:
            self.store.save("services", DEFAULT_SERVICES)
            configured = DEFAULT_SERVICES
        state = self.store.load("service_state", {})
        result = []
        for svc in configured:
            result.append({**svc, **state.get(svc["name"], {"status": "stopped"})})
        return result

    def start(self) -> dict:
        services = self.services()
        state = self.store.load("service_state", {})
        started = []
        for svc in services:
            state[svc["name"]] = {
                "status": "running",
                "started_at": datetime.now(timezone.utc).isoformat(),
                "heartbeat": datetime.now(timezone.utc).isoformat(),
                "instance_id": str(uuid4()),
            }
            started.append(svc["name"])
        self.store.save("service_state", state)
        return {"ok": True, "started": started}

    def stop(self) -> dict:
        state = self.store.load("service_state", {})
        for svc in self.services():
            state[svc["name"]] = {**state.get(svc["name"], {}), "status": "stopped", "stopped_at": datetime.now(timezone.utc).isoformat()}
        self.store.save("service_state", state)
        return {"ok": True, "stopped": [svc["name"] for svc in self.services()]}

    def heartbeat(self) -> dict:
        state = self.store.load("service_state", {})
        updated = []
        for svc in self.services():
            if state.get(svc["name"], {}).get("status") == "running":
                state[svc["name"]]["heartbeat"] = datetime.now(timezone.utc).isoformat()
                updated.append(svc["name"])
        self.store.save("service_state", state)
        return {"ok": True, "updated": updated}

    def health(self) -> dict:
        services = self.services()
        running = [s for s in services if s.get("status") == "running"]
        critical_down = [s["name"] for s in services if s.get("critical") and s.get("status") != "running"]
        status = "healthy" if not critical_down else "degraded"
        return {"status": status, "running": len(running), "total": len(services), "critical_down": critical_down}

    def recover(self) -> dict:
        state = self.store.load("service_state", {})
        recovered = []
        for svc in self.services():
            if svc.get("critical") and state.get(svc["name"], {}).get("status") != "running":
                state[svc["name"]] = {
                    "status": "running",
                    "recovered_at": datetime.now(timezone.utc).isoformat(),
                    "heartbeat": datetime.now(timezone.utc).isoformat(),
                    "instance_id": str(uuid4()),
                }
                recovered.append(svc["name"])
        self.store.save("service_state", state)
        return {"ok": True, "recovered": recovered}
