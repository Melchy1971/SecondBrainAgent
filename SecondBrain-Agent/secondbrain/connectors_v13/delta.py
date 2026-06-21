from datetime import datetime, timezone
from uuid import uuid4


class DeltaSyncEngine:
    def __init__(self, store):
        self.store = store

    def cursor(self, connector_id: str) -> dict:
        return self.store.load("cursors", {}).get(connector_id, {"cursor": None, "updated_at": None})

    def update_cursor(self, connector_id: str, cursor: str) -> dict:
        cursors = self.store.load("cursors", {})
        cursors[connector_id] = {"cursor": cursor, "updated_at": datetime.now(timezone.utc).isoformat()}
        self.store.save("cursors", cursors)
        return cursors[connector_id]

    def sync_result(self, connector_id: str, items: list[dict]) -> dict:
        run = {
            "id": str(uuid4()),
            "connector_id": connector_id,
            "items": len(items),
            "status": "success",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.store.append("sync_runs", run)
        self.update_cursor(connector_id, run["created_at"])
        return run

    def runs(self, limit: int = 50) -> list[dict]:
        return self.store.load("sync_runs", [])[-limit:]
