from datetime import datetime, timezone
from uuid import uuid4


class GoalEngine:
    def __init__(self, store):
        self.store = store

    def add_goal(self, name: str, target: float, current: float, unit: str, deadline_days: int = 90, priority: int = 3) -> dict:
        goal = {
            "id": str(uuid4()),
            "name": name,
            "target": target,
            "current": current,
            "unit": unit,
            "deadline_days": deadline_days,
            "priority": priority,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        return self.store.append("goals", goal)

    def goals(self) -> list[dict]:
        return self.store.load("goals", [])

    def forecast(self) -> list[dict]:
        result = []
        for goal in self.goals():
            remaining = max(float(goal["target"]) - float(goal["current"]), 0.0)
            priority = max(int(goal.get("priority", 3)), 1)
            estimated_days = int((remaining / priority) * 7) if remaining else 0
            probability = max(0.05, min(0.95, 1 - (estimated_days / max(int(goal.get("deadline_days", 90)), 1)) * 0.5))
            result.append({
                "goal_id": goal["id"],
                "name": goal["name"],
                "remaining": round(remaining, 2),
                "estimated_days": estimated_days,
                "deadline_days": goal.get("deadline_days", 90),
                "success_probability": round(probability, 3),
                "on_track": estimated_days <= int(goal.get("deadline_days", 90)),
            })
        return result
