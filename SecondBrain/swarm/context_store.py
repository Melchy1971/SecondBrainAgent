
from __future__ import annotations
from pathlib import Path
from typing import Any
from .common import JsonStore, now_iso

class SharedContextStore:
    def __init__(self, runtime_dir: str | Path):
        base = Path(runtime_dir) / "swarm_v124"
        self.contexts = JsonStore(base / "contexts.json", {})
        self.history = JsonStore(base / "context_history.json", [])

    def put(self, task_id: str, key: str, value: Any, agent: str = "system") -> dict[str, Any]:
        data = self.contexts.read()
        task = data.setdefault(task_id, {})
        task[key] = value
        self.contexts.write(data)
        return self.history.append({"task_id": task_id, "key": key, "agent": agent, "value": value, "created_at": now_iso()})

    def get_task(self, task_id: str) -> dict[str, Any]:
        return self.contexts.read().get(task_id, {})

    def status(self) -> dict[str, Any]:
        data = self.contexts.read()
        return {"component": "shared_context_store_v124", "tasks": len(data), "healthy": True}
