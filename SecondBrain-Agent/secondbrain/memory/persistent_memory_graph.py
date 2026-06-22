"""P3 v20.4 - Persistent Memory Graph Repository."""

import json
from pathlib import Path


class PersistentMemoryGraph:
    def __init__(self, path: str = "runtime/memory/memory_graph.json"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, graph: dict):
        self.path.write_text(json.dumps(graph, indent=2), encoding="utf-8")

    def load(self) -> dict:
        if not self.path.exists():
            return {}
        return json.loads(self.path.read_text(encoding="utf-8"))
