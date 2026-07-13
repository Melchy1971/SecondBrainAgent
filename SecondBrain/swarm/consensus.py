
from __future__ import annotations
from pathlib import Path
from typing import Any
from .common import JsonStore, new_id, now_iso

class ConsensusEngine:
    def __init__(self, runtime_dir: str | Path):
        self.store = JsonStore(Path(runtime_dir) / "swarm_v124" / "consensus.json", [])

    def evaluate(self, task_id: str, context: dict[str, Any]) -> dict[str, Any]:
        review = context.get("review", {})
        quality = float(review.get("quality_score", 0.0))
        passed = bool(review.get("passed", False))
        row = {
            "id": new_id("consensus"),
            "task_id": task_id,
            "decision": "accepted" if passed else "needs_revision",
            "quality_score": quality,
            "rationale": "review_passed" if passed else "review_failed",
            "created_at": now_iso(),
        }
        self.store.append(row)
        return row

    def list(self, task_id: str | None = None) -> list[dict[str, Any]]:
        rows = self.store.read()
        return [r for r in rows if r.get("task_id") == task_id] if task_id else rows
