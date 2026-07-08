
from __future__ import annotations
from pathlib import Path
from typing import Any
from .common import JsonStore, now_iso

class SwarmRecovery:
    def __init__(self, runtime_dir: str | Path):
        self.history = JsonStore(Path(runtime_dir) / "swarm_v124" / "recovery.json", [])

    def recover(self, task: dict[str, Any]) -> dict[str, Any]:
        row = {
            "task_id": task.get("id"),
            "previous_status": task.get("status"),
            "action": "marked_recoverable",
            "created_at": now_iso(),
        }
        self.history.append(row)
        return row
