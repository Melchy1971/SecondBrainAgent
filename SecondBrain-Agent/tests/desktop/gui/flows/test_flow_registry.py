import pytest

from secondbrain.desktop.gui.flows.flow_models import FlowStep
from secondbrain.desktop.gui.flows.flow_registry import DesktopFlow, DesktopFlowRegistry


def test_register_and_get_flow():
    registry = DesktopFlowRegistry()
    flow = DesktopFlow("f1", "Flow 1", [FlowStep("s1", "Step", lambda ctx: {})])
    registry.register(flow)
    assert registry.get("f1") is flow


def test_duplicate_step_ids_are_rejected():
    registry = DesktopFlowRegistry()
    flow = DesktopFlow("f1", "Flow 1", [FlowStep("s1", "A", lambda ctx: {}), FlowStep("s1", "B", lambda ctx: {})])
    with pytest.raises(ValueError):
        registry.register(flow)
