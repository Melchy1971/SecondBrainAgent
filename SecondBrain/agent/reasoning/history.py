"""v30.68 Reasoning Engine - ReasoningHistory.

Append-only JSONL of reasoning-session snapshots, so how a decision was reached
(thoughts, evidence, hypotheses, alternatives) is reconstructable afterwards.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def history_path(root: str | Path) -> Path:
    return Path(root).resolve() / "runtime" / "agent" / "reasoning" / "history.jsonl"


class ReasoningHistory:
    def __init__(self, project_root: str | Path):
        self.project_root = Path(project_root).resolve()
        self.path = history_path(self.project_root)

    def save(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(snapshot, ensure_ascii=False) + "\n")
        return snapshot

    def list(self, *, limit: int = 50) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        rows: list[dict[str, Any]] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return rows[-max(1, int(limit)):]

    def get(self, session_id: str) -> dict[str, Any] | None:
        for row in reversed(self.list(limit=100000)):
            if row.get("id") == session_id:
                return row
        return None
