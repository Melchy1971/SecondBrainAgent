from dataclasses import replace
from .models import TwinState, Project
from .forecast import ForecastEngine
from .risk import RiskModel


class ScenarioEngine:
    def __init__(self):
        self.forecast = ForecastEngine()
        self.risk = RiskModel()

    def simulate_add_project(self, state: TwinState, project: Project) -> dict:
        simulated = replace(state, projects=[*state.projects, project])
        return {
            "scenario": "add_project",
            "project": project.name,
            "capacity": self.forecast.capacity_load(simulated),
            "risk": self.risk.evaluate(simulated),
            "goals": self.forecast.goal_forecast(simulated),
        }

    def compare(self, base: TwinState, candidate: TwinState) -> dict:
        base_capacity = self.forecast.capacity_load(base)
        candidate_capacity = self.forecast.capacity_load(candidate)
        base_risk = self.risk.evaluate(base)
        candidate_risk = self.risk.evaluate(candidate)
        return {
            "capacity_delta_hours": round(candidate_capacity["free_hours"] - base_capacity["free_hours"], 2),
            "risk_delta": round(candidate_risk["risk_score"] - base_risk["risk_score"], 3),
            "candidate_overloaded": candidate_capacity["overloaded"],
        }
