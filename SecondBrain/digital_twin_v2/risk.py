from .models import TwinState


class RiskModel:
    def evaluate(self, state: TwinState) -> dict:
        total_project_risk = sum(p.risk * p.weekly_hours for p in state.projects)
        total_hours = sum(p.weekly_hours for p in state.projects) or 1.0
        weighted_project_risk = total_project_risk / total_hours
        load = (sum(p.weekly_hours for p in state.projects) + sum(h.weekly_hours for h in state.habits)) / max(state.weekly_capacity_hours, 0.01)
        energy_risk = max(0.0, 1.0 - state.energy_level)
        score = min(1.0, (weighted_project_risk * 0.45) + (max(load - 0.8, 0) * 0.35) + (energy_risk * 0.2))
        level = "low" if score < 0.35 else "medium" if score < 0.7 else "high"
        return {
            "risk_score": round(score, 3),
            "risk_level": level,
            "load_ratio": round(load, 3),
            "energy_risk": round(energy_risk, 3),
        }
