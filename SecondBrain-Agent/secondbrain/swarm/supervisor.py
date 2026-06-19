
from __future__ import annotations
from typing import Any
from .common import new_id, now_iso

class SupervisorAgent:
    name = "supervisor"

    def create_task(self, objective: str, priority: str = "normal") -> dict[str, Any]:
        return {
            "id": new_id("swarm"),
            "objective": objective.strip(),
            "priority": priority,
            "status": "created",
            "created_at": now_iso(),
            "updated_at": now_iso(),
        }

    def analyze(self, task: dict[str, Any]) -> dict[str, Any]:
        objective = task.get("objective", "")
        return {
            "agent": self.name,
            "task_id": task.get("id"),
            "needs_research": any(x in objective.lower() for x in ["recherch", "suche", "analyse", "vergleich", "research"]),
            "risk_level": 1 if len(objective) < 240 else 2,
            "recommended_flow": ["planner", "researcher", "executor", "reviewer", "memory_curator"],
        }
