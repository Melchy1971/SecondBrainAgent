from secondbrain.digital_twin_v113 import DigitalTwin, parse_scenario_change
from secondbrain.decision_engine_v113 import DecisionEngine, parse_option
from secondbrain.launcher_runtime_v113 import SecondBrainLauncherV113


def test_twin_capacity_and_simulation(tmp_path):
    twin = DigitalTwin(tmp_path)
    twin.set_capacity(40, fixed_commitments_hours=10, recovery_buffer_hours=5)
    twin.add_project("Core", 10, risk_level=2)
    result = twin.simulate("Add Mobile", [parse_scenario_change("Mobile:8:3")])
    assert result.capacity_hours == 25
    assert result.used_hours == 18
    assert result.overload_hours == 0
    assert result.impact in {"low_risk", "medium_risk", "high_risk"}


def test_twin_detects_overload(tmp_path):
    twin = DigitalTwin(tmp_path)
    twin.set_capacity(20, fixed_commitments_hours=5, recovery_buffer_hours=5)
    twin.add_project("A", 8)
    result = twin.simulate("Too much", [parse_scenario_change("B:8:2")])
    assert result.overload_hours == 6
    assert result.impact == "high_risk"
    assert result.bottlenecks


def test_decision_engine_ranks_options(tmp_path):
    twin = DigitalTwin(tmp_path)
    twin.set_capacity(40, 10, 5)
    engine = DecisionEngine(tmp_path, twin)
    result = engine.evaluate("Was zuerst?", [parse_option("A:2:5:1:5:5"), parse_option("B:10:3:4:3:2")])
    assert result.recommended_option == "A"
    assert result.ranking[0]["option"] == "A"


def test_launcher_twin_commands(tmp_path):
    launcher = SecondBrainLauncherV113(tmp_path)
    cap = launcher.twin_capacity(30, 5, 5)
    assert cap["usable_hours"] == 20
    project = launcher.twin_add_project("Jarvis", 4)
    assert project["name"] == "Jarvis"
    snapshot = launcher.twin_snapshot()
    assert snapshot["active_projects"] == 1


def test_launcher_decision(tmp_path):
    launcher = SecondBrainLauncherV113(tmp_path)
    launcher.twin_capacity(40, 10, 5)
    result = launcher.decision_evaluate("Priorisieren", ["A:3:5:1:5:5", "B:20:3:4:3:2"])
    assert result["recommended_option"] == "A"
    assert len(result["ranking"]) == 2
