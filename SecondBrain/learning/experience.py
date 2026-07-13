from .store import LearningStore
from .models import Experience


class ExperienceStore:
    def __init__(self, store: LearningStore):
        self.store = store

    def add(self, experience: Experience) -> dict:
        return self.store.append("experiences", experience.to_dict())

    def list(self, limit: int = 50) -> list[dict]:
        return self.store.load("experiences", [])[-limit:]
