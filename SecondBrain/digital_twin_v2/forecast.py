from __future__ import annotations
from .models import TwinState


class ForecastEngine:
    def capacity_load(self, state: TwinState) -> dict:
        project_hours = sum(p.weekly_hours for p in state.projects)
        habit_hours = sum(h.weekly_hours for h in state.habits)
        used = project_hours + habit_hours
        capacity = max(state.weekly_capacity_hours, 0.01)
        load_ratio = used / capacity
        return {
            "capacity_hours": round(capacity, 2),
            "used_hours": round(used, 2),
            "free_hours": round(capacity - used, 2),
            "load_ratio": round(load_ratio, 3),
            "overloaded": load_ratio > 1.0,
        }

    def goal_forecast(self, state: TwinState) -> list[dict]:
        load = self.capacity_load(state)["load_ratio"]
        energy_modifier = max(0.2, min(1.2, state.energy_level))
        forecasts = []
        for goal in state.goals:
            remaining = max(goal.target_value - goal.current_value, 0.0)
            base_velocity = max(goal.priority, 1) * energy_modifier / max(load, 0.5)
            estimated_days = int((remaining / max(base_velocity, 0.01)) * 7) if remaining else 0
            forecasts.append({
                "goal_id": goal.id,
                "name": goal.name,
                "remaining": round(remaining, 2),
                "estimated_days": estimated_days,
                "deadline_days": goal.deadline_days,
                "on_track": estimated_days <= goal.deadline_days,
            })
        return forecasts
