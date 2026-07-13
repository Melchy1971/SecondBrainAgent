from __future__ import annotations

from secondbrain.agent.coordination import (
    Coordinator,
    CriticAgent,
    ExecutorAgent,
    ImportAgent,
    MemoryAgent,
    PlannerAgent,
    ReviewerAgent,
    SearchAgent,
)
from secondbrain.agent.coordination.models import (
    KIND_CRITIQUE,
    KIND_EXECUTE,
    KIND_IMPORT_CHECK,
    KIND_MEMORY_RECALL,
    KIND_MEMORY_STORE,
    KIND_PLAN,
    KIND_REVIEW,
    KIND_SEARCH,
    AgentTask,
)

from tests._coord_fakes import RISKY_STEPS, FakePlanner


def _ws(tmp_path):
    return Coordinator(tmp_path, agents=[]).workspace


def test_capabilities_are_distinct():
    assert PlannerAgent().can_handle(KIND_PLAN)
    assert CriticAgent().can_handle(KIND_CRITIQUE)
    assert MemoryAgent().can_handle(KIND_MEMORY_STORE)
    assert MemoryAgent().can_handle(KIND_MEMORY_RECALL)
    assert not PlannerAgent().can_handle(KIND_EXECUTE)


def test_planner_agent_uses_planner(tmp_path):
    ws = _ws(tmp_path)
    agent = PlannerAgent(planner=FakePlanner())
    res = agent.handle(AgentTask.create(KIND_PLAN, {"goal": "Ziel"}), ws)
    assert res.ok
    assert res.output["steps"]
    assert ws.context.get("plan")["goal"] == "Ziel"


def test_critic_flags_high_risk(tmp_path):
    ws = _ws(tmp_path)
    plan = {"steps": RISKY_STEPS}
    res = CriticAgent().handle(AgentTask.create(KIND_CRITIQUE, {"plan": plan}), ws)
    assert res.ok
    assert res.output["severity"] == "high"
    assert any(r.startswith("high_risk_step") for r in res.output["risks"])


def test_critic_low_severity_for_clean_plan(tmp_path):
    ws = _ws(tmp_path)
    plan = {"steps": [{"id": "s1", "risk_level": "low", "expected_output": "x"}]}
    res = CriticAgent().handle(AgentTask.create(KIND_CRITIQUE, {"plan": plan}), ws)
    assert res.output["severity"] == "low"


def test_reviewer_approves_complete_plan(tmp_path):
    ws = _ws(tmp_path)
    plan = {"status": "validated", "steps": [{"id": "s1", "expected_output": "done"}]}
    res = ReviewerAgent().handle(AgentTask.create(KIND_REVIEW, {"plan": plan}), ws)
    assert res.output["approved"] is True


def test_reviewer_flags_missing_output(tmp_path):
    ws = _ws(tmp_path)
    plan = {"status": "validated", "steps": [{"id": "s1", "expected_output": ""}]}
    res = ReviewerAgent().handle(AgentTask.create(KIND_REVIEW, {"plan": plan}), ws)
    assert res.output["approved"] is False
    assert any("missing_expected_output" in n for n in res.output["notes"])


def test_executor_runs_workflow(tmp_path):
    ws = _ws(tmp_path)
    task = AgentTask.create(KIND_EXECUTE, {"objective": "obj",
                                           "steps": [{"id": "a", "name": "A"}, {"id": "b", "name": "B"}]})
    res = ExecutorAgent().handle(task, ws)
    assert res.ok
    assert res.output["state"] == "COMPLETED"


def test_memory_agent_store_and_recall(tmp_path):
    ws = _ws(tmp_path)
    stored = MemoryAgent().handle(AgentTask.create(KIND_MEMORY_STORE,
                                                   {"text": "SAP Migration ist Prioritaet"}), ws)
    assert stored.output["stored"] is True
    recalled = MemoryAgent().handle(AgentTask.create(KIND_MEMORY_RECALL, {"query": "SAP"}), ws)
    assert recalled.output["count"] >= 1


def test_search_agent_uses_shared_memory(tmp_path):
    ws = _ws(tmp_path)
    ws.memory.remember("Der Watcher laeuft stabil", source="log")
    res = SearchAgent().handle(AgentTask.create(KIND_SEARCH, {"query": "Watcher"}), ws)
    assert res.ok
    assert res.output["count"] >= 1


def test_import_agent_reports_healthy_on_empty_queue(tmp_path):
    ws = _ws(tmp_path)
    res = ImportAgent().handle(AgentTask.create(KIND_IMPORT_CHECK, {}), ws)
    assert res.ok
    assert res.output["healthy"] is True
