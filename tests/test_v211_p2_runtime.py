from secondbrain.agent.tool_permissions import ToolPermissionManager
from secondbrain.agent.approval_system import ApprovalSystem
from secondbrain.agent.reasoning_runtime import ReasoningRuntime
from secondbrain.agent.recovery_engine import RecoveryEngine
from secondbrain.gates.p2_production_gate import P2ProductionGate


def test_permissions():
    manager = ToolPermissionManager()
    manager.deny("delete")
    assert manager.is_allowed("read")
    assert not manager.is_allowed("delete")


def test_approval_system():
    approval = ApprovalSystem()
    approval.approve("a1")
    assert approval.is_approved("a1")


def test_reasoning_runtime():
    result = ReasoningRuntime().execute(["step1", "step2"])
    assert result["steps"] == 2


def test_recovery_engine():
    result = RecoveryEngine().recover(ValueError("boom"))
    assert result["status"] == "RECOVERED"


def test_p2_gate():
    caps = {k: True for k in P2ProductionGate.REQUIRED}
    assert P2ProductionGate().evaluate(caps)["status"] == "PASS"
