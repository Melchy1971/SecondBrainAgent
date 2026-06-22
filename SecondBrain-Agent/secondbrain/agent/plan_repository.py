"""P2 v21.3 - Plan Persistence."""

import json
from pathlib import Path


class PlanRepository:
    def __init__(self, path: str = "runtime/agent/plans.json"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, plan: dict):
        self.path.write_text(json.dumps(plan, indent=2), encoding="utf-8")

    def load(self):
        if not self.path.exists():
            return {}
        return json.loads(self.path.read_text(encoding="utf-8"))
