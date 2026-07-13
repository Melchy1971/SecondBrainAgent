from .store import TwinStore
from .models import Goal, Project, Habit
from .forecast import ForecastEngine
from .risk import RiskModel
from .scenario import ScenarioEngine
from .decision import DecisionSimulator


class DigitalTwinV2:
    def __init__(self, root="."):
        self.store = TwinStore(root)
        self.forecast = ForecastEngine()
        self.risk = RiskModel()
        self.scenario = ScenarioEngine()
        self.decision = DecisionSimulator()

    def status(self) -> dict:
        state = self.store.load()
        return {
            "capacity": self.forecast.capacity_load(state),
            "risk": self.risk.evaluate(state),
            "goals": len(state.goals),
            "projects": len(state.projects),
            "habits": len(state.habits),
        }

    def add_goal(self, goal: Goal) -> dict:
        state = self.store.load()
        state.goals.append(goal)
        self.store.save(state)
        return {"ok": True, "goal": goal.name}

    def add_project(self, project: Project) -> dict:
        state = self.store.load()
        state.projects.append(project)
        self.store.save(state)
        return {"ok": True, "project": project.name}

    def add_habit(self, habit: Habit) -> dict:
        state = self.store.load()
        state.habits.append(habit)
        self.store.save(state)
        return {"ok": True, "habit": habit.name}

    def forecast_goals(self) -> list[dict]:
        return self.forecast.goal_forecast(self.store.load())

    def simulate_project(self, project: Project) -> dict:
        return self.scenario.simulate_add_project(self.store.load(), project)

    def evaluate_project(self, project: Project) -> dict:
        return self.decision.evaluate_project(self.store.load(), project)
