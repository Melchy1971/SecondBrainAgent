from secondbrain.digital_twin_v2 import DigitalTwinV2
from secondbrain.digital_twin_v2.models import Goal, Project, Habit


def test_status_empty(tmp_path):
    twin = DigitalTwinV2(tmp_path)
    status = twin.status()
    assert status["goals"] == 0
    assert status["capacity"]["capacity_hours"] == 20.0


def test_goal_forecast(tmp_path):
    twin = DigitalTwinV2(tmp_path)
    twin.add_goal(Goal("g1", "TTR 1200", 1200, 1147, "points", 120, 4))
    forecast = twin.forecast_goals()
    assert forecast[0]["goal_id"] == "g1"


def test_project_decision(tmp_path):
    twin = DigitalTwinV2(tmp_path)
    decision = twin.evaluate_project(Project("p1", "Desktop OS", 3, 0.8, 0.2, 60, 0.8))
    assert decision["recommendation"] in {"accept", "review", "reject"}


def test_simulation_overload(tmp_path):
    twin = DigitalTwinV2(tmp_path)
    sim = twin.simulate_project(Project("p2", "Too much", 99, 0.8, 0.9, 30, 0.8))
    assert sim["capacity"]["overloaded"] is True
