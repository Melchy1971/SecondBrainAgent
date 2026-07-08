from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class ExecutionHistoryEntry:
    plan_id: str
    status: str
    completed_tasks: int
    failed_tasks: int
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "status": self.status,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }


class ExecutionHistory:
    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path else None
        self.entries: list[ExecutionHistoryEntry] = []

    def append(self, entry: ExecutionHistoryEntry) -> None:
        self.entries.append(entry)

    def save(self) -> None:
        if not self.path:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps([e.to_dict() for e in self.entries], indent=2), encoding="utf-8")

    def load(self) -> list[dict[str, Any]]:
        if not self.path or not self.path.exists():
            return []
        return json.loads(self.path.read_text(encoding="utf-8"))
