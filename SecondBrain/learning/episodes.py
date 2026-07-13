from datetime import datetime, timezone
from uuid import uuid4
from .store import LearningStore


class EpisodeMemory:
    def __init__(self, store: LearningStore):
        self.store = store

    def create(self, title: str, experience_ids: list[str], summary: str) -> dict:
        item = {
            "id": str(uuid4()),
            "title": title,
            "experience_ids": experience_ids,
            "summary": summary,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        return self.store.append("episodes", item)

    def list(self, limit: int = 50) -> list[dict]:
        return self.store.load("episodes", [])[-limit:]
