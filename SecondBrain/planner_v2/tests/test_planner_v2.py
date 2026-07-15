"""Sprint 50 acceptance tests - validated graph-based planner v2."""

from __future__ import annotations

from threading import Barrier, Lock
from time import sleep

import pytest

from secondbrain.planner_v2.models import (
    Budget, NodeStatus, PlanNode, PlanStatus, RetryPolicy, RiskLevel,
)
from secondbrain.planner_v2.service import Planner
from secondbrain.planner_v2.gui import PlannerViewModel, render_plan_html

WS = "ws-1"


def _planner(**kw):
    kw.setdefault("available_tools", ["fetch", "summarize", "send", "backup", "alt_send"])
    return Planner(**kw)


def _node(nid, **kw):
    kw.setdefault("tool", "fetch")
    kw.setdefault("input", {"x": 1})
    return PlanNode(node_id=nid, objective=f"obj {nid}", **kw)


def _tools(calls=None):
    log = calls if calls is not None else []
    def make(name, fail=False):
        def fn(inp):
            log.append(name)
            if fail:
                raise RuntimeError("boom")
            return {"ok": name}
        return fn
    return log, make


class ApprovalAuthority:
    def __init__(self, allowed):
        self.allowed = set(allowed)
        self.claimed = set()

    def claim(self, *, plan, node):
        binding = (plan.plan_id, plan.workspace_id, node.node_id)
        if node.node_id not in self.allowed or binding in self.claimed:
            return False
        self.claimed.add(binding)
        return True


# 1: multi-step plan is created
def test_multistep_plan_created():
    p = _planner()
    plan = p.create_plan(goal="G", workspace_id=WS, nodes=[
        _node("a"), _node("b", dependencies=["a"]), _node("c", dependencies=["b"])])
    assert len(plan.nodes) == 3
    assert p.is_valid(plan)
    layers = p.execution_layers(plan)
    assert layers == [["a"], ["b"], ["c"]]


# 2: cycle detected
def test_cycle_detected():
    p = _planner()
    plan = p.create_plan(goal="G", workspace_id=WS, nodes=[
        _node("a", dependencies=["c"]), _node("b", dependencies=["a"]), _node("c", dependencies=["b"])])
    issues = p.validate_plan(plan)
    assert any(i["type"] == "cycle" for i in issues)
    assert plan.status == PlanStatus.INVALID.value


# 3: independent steps can run in parallel
def test_independent_parallel():
    p = _planner()
    plan = p.create_plan(goal="G", workspace_id=WS, nodes=[
        _node("a"), _node("b"), _node("c", dependencies=["a", "b"])])
    layers = p.execution_layers(plan)
    assert set(layers[0]) == {"a", "b"}  # independent
    groups = p.parallel_groups(plan)
    assert any(set(g) == {"a", "b"} for g in groups)


def test_independent_nodes_actually_run_in_parallel():
    p = _planner(max_parallelism=2)
    plan = p.create_plan(goal="G", workspace_id=WS, nodes=[_node("a"), _node("b")])
    barrier = Barrier(2, timeout=1)

    def rendezvous(inp):
        barrier.wait()
        return inp

    res = p.execute_plan(plan, tools={"fetch": rendezvous})
    assert res["status"] == PlanStatus.COMPLETED.value
    assert res["executed"] == ["a", "b"]


def test_shared_resource_is_serialized():
    p = _planner(max_parallelism=2)
    plan = p.create_plan(goal="G", workspace_id=WS, nodes=[
        _node("a", resource_locks=["workspace:file"]),
        _node("b", resource_locks=["workspace:file"]),
    ])
    guard = Lock()
    state = {"active": 0, "peak": 0}

    def guarded(inp):
        with guard:
            state["active"] += 1
            state["peak"] = max(state["peak"], state["active"])
        sleep(0.02)
        with guard:
            state["active"] -= 1
        return inp

    res = p.execute_plan(plan, tools={"fetch": guarded})
    assert res["status"] == PlanStatus.COMPLETED.value
    assert state["peak"] == 1


def test_parallel_success_is_checkpointed_when_sibling_fails():
    p = _planner(max_parallelism=2)
    plan = p.create_plan(goal="G", workspace_id=WS, nodes=[
        _node("a", tool="fetch"), _node("b", tool="summarize")])

    def fail(inp):
        raise RuntimeError("boom")

    res = p.execute_plan(plan, tools={"fetch": lambda inp: inp, "summarize": fail})
    assert res["status"] == PlanStatus.RECOVERY_REQUIRED.value
    assert res["executed"] == ["a"]
    assert res["failed"] == ["b"]
    assert plan.checkpoint == ["a"]


# 4: risky step pauses (requires approval)
def test_risky_step_pauses():
    p = _planner()
    plan = p.create_plan(goal="G", workspace_id=WS, nodes=[
        _node("a"),
        _node("s", tool="send", risk=RiskLevel.HIGH.value, approval_required=True, dependencies=["a"])])
    log, make = _tools()
    tools = {"fetch": make("fetch"), "send": make("send")}
    res = p.execute_plan(plan, tools=tools)
    assert "s" in res["paused"]
    assert plan.node("s").status == NodeStatus.WAITING_FOR_APPROVAL.value
    assert "send" not in log  # never executed without approval


# 5: cost limit respected
def test_cost_limit():
    p = _planner()
    plan = p.create_plan(goal="G", workspace_id=WS, budget=Budget(max_cost=10.0), nodes=[
        _node("a", estimated_cost=6.0), _node("b", dependencies=["a"], estimated_cost=6.0)])
    log, make = _tools()
    res = p.execute_plan(plan, tools={"fetch": make("fetch")})
    assert res["status"] == "budget_exceeded"
    assert res["executed"] == ["a"]
    assert res["cost"] <= 10.0
    assert log == ["fetch"]  # only the first node ran


# 5b: validation flags cost over budget
def test_validate_cost_limit():
    p = _planner()
    plan = p.create_plan(goal="G", workspace_id=WS, budget=Budget(max_cost=5.0),
                         nodes=[_node("a", estimated_cost=9.0)])
    assert any(i["type"] == "cost_limit" for i in p.validate_plan(plan))


# 6: simulation executes no tools
def test_simulation_no_execution():
    p = _planner()
    plan = p.create_plan(goal="G", workspace_id=WS, nodes=[_node("a"), _node("b", dependencies=["a"])])
    log, make = _tools()
    sim = p.simulate_plan(plan)
    assert sim["executed"] is False
    assert len(sim["planned_actions"]) == 2
    assert log == []  # nothing ran


# 7: resume continues from checkpoint
def test_resume_from_checkpoint():
    p = _planner()
    plan = p.create_plan(goal="G", workspace_id=WS, nodes=[
        _node("a"),
        _node("s", tool="send", risk=RiskLevel.HIGH.value, approval_required=True, dependencies=["a"]),
        _node("c", dependencies=["s"])])
    log, make = _tools()
    tools = {"fetch": make("fetch"), "send": make("send")}
    r1 = p.execute_plan(plan, tools=tools)
    assert r1["executed"] == ["a"] and "s" in r1["paused"]
    assert plan.checkpoint == ["a"]
    # approve and resume -> a is skipped (checkpoint), s and c run
    r2 = p.resume_plan(plan, tools=tools, approval_authority=ApprovalAuthority(["s"]))
    assert "a" not in r2["executed"]
    assert set(r2["executed"]) == {"s", "c"}
    assert plan.status == PlanStatus.COMPLETED.value


# 8: recovery uses alternative path
def test_recovery_alt_path():
    p = _planner()
    plan = p.create_plan(goal="G", workspace_id=WS, nodes=[
        _node("x", tool="send", alt_tools=["alt_send"])])
    log = []
    tools = {"send": (lambda inp: (_ for _ in ()).throw(RuntimeError("down"))),
             "alt_send": (lambda inp: log.append("alt_send") or {"ok": 1})}
    res = p.execute_plan(plan, tools=tools)
    assert res["status"] == PlanStatus.COMPLETED.value
    assert "x" in res["executed"]
    assert log == ["alt_send"]
    assert any(a["event"] == "attempt_failed" for a in plan.audit)
    assert any("alt:alt_send" in a["detail"] for a in plan.audit if a["event"] == "completed")


# 8b: retry policy retries before failing over
def test_retry_before_failover():
    p = _planner()
    plan = p.create_plan(goal="G", workspace_id=WS, nodes=[
        _node("x", tool="fetch", retry_policy=RetryPolicy(max_attempts=2))])
    state = {"n": 0}
    def flaky(inp):
        state["n"] += 1
        if state["n"] < 2:
            raise RuntimeError("transient")
        return {"ok": 1}
    res = p.execute_plan(plan, tools={"fetch": flaky})
    assert res["status"] == PlanStatus.COMPLETED.value
    assert state["n"] == 2


# 9: audit records every step
def test_audit_every_step():
    p = _planner()
    plan = p.create_plan(goal="G", workspace_id=WS, nodes=[_node("a"), _node("b", dependencies=["a"])])
    log, make = _tools()
    p.execute_plan(plan, tools={"fetch": make("fetch")})
    completed = [a["node"] for a in plan.audit if a["event"] == "completed"]
    assert "a" in completed and "b" in completed
    assert any(a["event"] == "created" for a in plan.audit)


# 10: approval cannot be bypassed by parallelisation
def test_approval_not_bypassed_by_parallel():
    p = _planner()
    # a and s are in the SAME layer (both independent), s requires approval
    plan = p.create_plan(goal="G", workspace_id=WS, nodes=[
        _node("a"),
        _node("s", tool="send", risk=RiskLevel.HIGH.value, approval_required=True)])
    log, make = _tools()
    tools = {"fetch": make("fetch"), "send": make("send")}
    res = p.execute_plan(plan, tools=tools)
    assert "a" in res["executed"]      # independent sibling runs
    assert "s" in res["paused"]        # approval node held
    assert "send" not in log           # not executed despite parallel layer
    # s is excluded from concurrent groups
    assert all("s" not in g for g in p.parallel_groups(plan))


def test_workspace_crossing_and_unsafe_retry_are_blocked():
    p = _planner()
    plan = p.create_plan(goal="G", workspace_id=WS, nodes=[
        _node("x", input={"workspace_id": "ws-2"}),
        _node("s", tool="send", retry_policy=RetryPolicy(max_attempts=3), approval_required=True),
    ])
    types = {issue["type"] for issue in p.validate_plan(plan)}
    assert {"workspace_crossing", "unsafe_retry"} <= types


# cancel stops controlled
def test_cancel_controlled():
    p = _planner()
    plan = p.create_plan(goal="G", workspace_id=WS, nodes=[_node("a"), _node("b", dependencies=["a"])])
    log, make = _tools()
    res = p.execute_plan(plan, tools={"fetch": make("fetch")}, cancel=True)
    assert res["status"] == PlanStatus.CANCELLED.value
    assert log == []


# missing tool / scope validation
def test_missing_tool_and_scope():
    p = Planner(available_tools=["fetch"], tool_scopes={"send": "mail.send"}, granted_scopes=[])
    plan = p.create_plan(goal="G", workspace_id=WS, nodes=[
        _node("a", tool="unknown"), _node("s", tool="send", approval_required=True, dependencies=["a"])])
    issues = p.validate_plan(plan)
    assert any(i["type"] == "missing_tool" for i in issues)
    assert any(i["type"] == "missing_scope" for i in issues)


# workspace stored
def test_workspace_and_gui():
    p = _planner()
    plan = p.create_plan(goal="Ziel", workspace_id=WS, nodes=[
        _node("a"), _node("b"), _node("c", dependencies=["a", "b"])])
    view = PlannerViewModel(p).build(plan)
    assert view["goal"] == "Ziel"
    html_out = render_plan_html(view)
    assert "Ausführungsebenen" in html_out and "Ebene 0" in html_out


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
