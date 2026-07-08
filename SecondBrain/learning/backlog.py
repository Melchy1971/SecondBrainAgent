from datetime import datetime, timezone
from uuid import uuid4
from .store import LearningStore


class LearningBacklog:
    def __init__(self, store: LearningStore):
        self.store = store

    def from_reflection(self, reflection: dict) -> list[dict]:
        backlog = self.store.load("backlog", [])
        created = []
        for rec in reflection.get("recommendations", []):
            item = {
                "id": str(uuid4()),
                "title": f"Improve {rec.get('capability', 'unknown')}",
                "source": "learning_reflection",
                "priority": rec.get("priority", "medium"),
                "status": "open",
                "details": rec,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            backlog.append(item)
            created.append(item)
        self.store.save("backlog", backlog)
        return created

    def list(self) -> list[dict]:
        return self.store.load("backlog", [])
