from datetime import datetime, timezone
from uuid import uuid4


SYNC_DOMAINS = ["memories", "projects", "tasks", "notifications", "knowledge_graph", "agent_state", "settings", "sessions"]


class SyncEngineV2:
    def __init__(self, store):
        self.store = store

    def status(self) -> dict:
        state = self.store.load("sync_state", {})
        conflicts = self.store.load("sync_conflicts", [])
        return {
            "domains": SYNC_DOMAINS,
            "last_sync": state.get("last_sync"),
            "conflicts": len(conflicts),
            "protocol": "local-sync-v2",
        }

    def sync_now(self, device_id: str | None = None) -> dict:
        run = {
            "id": str(uuid4()),
            "device_id": device_id,
            "domains": SYNC_DOMAINS,
            "status": "success",
            "strategy": "timestamp_then_semantic_merge_queue",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.store.append("sync_runs", run)
        self.store.save("sync_state", {"last_sync": run["created_at"], "last_run_id": run["id"]})
        return run

    def add_conflict(self, domain: str, local_value: dict, remote_value: dict) -> dict:
        conflict = {
            "id": str(uuid4()),
            "domain": domain,
            "local_value": local_value,
            "remote_value": remote_value,
            "status": "needs_approval",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        return self.store.append("sync_conflicts", conflict)

    def conflicts(self) -> list[dict]:
        return self.store.load("sync_conflicts", [])
