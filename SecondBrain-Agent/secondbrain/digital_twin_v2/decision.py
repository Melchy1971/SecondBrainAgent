from .models import TwinState, Project
from .scenario import ScenarioEngine


class DecisionSimulator:
    def __init__(self):
        self.scenarios = ScenarioEngine()

    def evaluate_project(self, state: TwinState, project: Project) -> dict:
        result = self.scenarios.simulate_add_project(state, project)
        risk_score = result["risk"]["risk_score"]
        load_ratio = result["capacity"]["load_ratio"]
        strategic = project.strategic_score
        decision_score = max(0.0, min(1.0, strategic * 0.5 + project.impact * 0.3 - risk_score * 0.15 - max(load_ratio - 1.0, 0) * 0.3))
        recommendation = "accept" if decision_score >= 0.65 and not result["capacity"]["overloaded"] else "review" if decision_score >= 0.45 else "reject"
        return {
            "decision_score": round(decision_score, 3),
            "recommendation": recommendation,
            "simulation": result,
        }
