from secondbrain.desktop.gui.flows.flow_models import FlowStep, FlowStatus
from secondbrain.desktop.gui.flows.flow_registry import DesktopFlow, DesktopFlowRegistry
from secondbrain.desktop.gui.flows.flow_runner import DesktopFlowRunner


def test_runner_passes_context_between_steps():
    registry = DesktopFlowRegistry()
    registry.register(DesktopFlow("f", "F", [FlowStep("a", "A", lambda ctx: {"x": 1}), FlowStep("b", "B", lambda ctx: {"y": ctx["x"] + 1})]))
    runner = DesktopFlowRunner(registry)
    result = runner.run("f")
    assert result.status == FlowStatus.PASSED
    assert result.context["y"] == 2
    assert runner.events[0]["type"] == "FLOW_STARTED"


def test_runner_stops_on_required_failure():
    registry = DesktopFlowRegistry()
    def fail(_ctx):
        raise RuntimeError("boom")
    registry.register(DesktopFlow("f", "F", [FlowStep("a", "A", fail), FlowStep("b", "B", lambda ctx: {})]))
    result = DesktopFlowRunner(registry).run("f")
    assert result.status == FlowStatus.FAILED
    assert len(result.steps) == 1
    assert result.failed_steps[0].error == "boom"
