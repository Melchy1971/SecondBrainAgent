"""P3 v20.2 - Persistent Memory Repository."""

import json
from pathlib import Path


class PersistentMemoryRepository:
    def __init__(self, path: str = "runtime/memory/memory_repository.json"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, payload: dict):
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def load(self) -> dict:
        if not self.path.exists():
            return {}
        return json.loads(self.path.read_text(encoding="utf-8"))
