from secondbrain.agent.execution_queue import ExecutionQueue
from secondbrain.agent.state_machine import AgentStateMachine, AgentState
from secondbrain.agent.tool_invocation_audit import ToolInvocationAudit
from secondbrain.gates.p2_maturity_gate import P2MaturityGate


def test_execution_queue():
    q = ExecutionQueue()
    q.enqueue("a")
    assert q.dequeue() == "a"


def test_state_machine():
    sm = AgentStateMachine()
    assert sm.transition(AgentState.PLANNING) == AgentState.PLANNING


def test_tool_audit():
    audit = ToolInvocationAudit()
    audit.record("search", "PASS")
    assert len(audit.list()) == 1


def test_p2_maturity_gate():
    caps = {k: True for k in P2MaturityGate.REQUIRED}
    assert P2MaturityGate().evaluate(caps)["status"] == "PASS"
