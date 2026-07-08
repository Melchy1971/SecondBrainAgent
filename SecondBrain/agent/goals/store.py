"""v30.65 Agent Goal Tracking - persistence.

``goals.json`` holds the goal registry; ``reviews.jsonl`` is an append-only trail
of generated goal reports. Writes are atomic (temp + replace).
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from .models import Goal, GoalReview


def base_dir(root: str | Path) -> Path:
    return Path(root).resolve() / "runtime" / "agent" / "goals"


class GoalStore:
    def __init__(self, project_root: str | Path):
        self.project_root = Path(project_root).resolve()
        self.dir = base_dir(self.project_root)
        self.goals_path = self.dir / "goals.json"
        self.reviews_path = self.dir / "reviews.jsonl"

    def load_goals(self) -> dict[str, Goal]:
        if not self.goals_path.exists():
            return {}
        try:
            raw = json.loads(self.goals_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
        return {gid: Goal.from_dict(data) for gid, data in raw.items()}

    def save_goals(self, goals: dict[str, Goal]) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        payload = {gid: goal.to_dict() for gid, goal in goals.items()}
        tmp = self.goals_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, self.goals_path)

    def get(self, goal_id: str) -> Goal | None:
        return self.load_goals().get(goal_id)

    def upsert(self, goal: Goal) -> Goal:
        goals = self.load_goals()
        goals[goal.id] = goal
        self.save_goals(goals)
        return goal

    def delete(self, goal_id: str) -> bool:
        goals = self.load_goals()
        if goal_id in goals:
            del goals[goal_id]
            self.save_goals(goals)
            return True
        return False

    def append_review(self, review: GoalReview) -> GoalReview:
        self.dir.mkdir(parents=True, exist_ok=True)
        with self.reviews_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(review.to_dict(), ensure_ascii=False) + "\n")
        return review

    def reviews(self, goal_id: str | None = None, *, limit: int = 100) -> list[GoalReview]:
        if not self.reviews_path.exists():
            return []
        rows: list[GoalReview] = []
        for line in self.reviews_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            if goal_id is None or data.get("goal_id") == goal_id:
                rows.append(GoalReview.from_dict(data))
        return rows[-max(1, int(limit)):]
