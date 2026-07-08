from __future__ import annotations

from secondbrain.agent.coordination import (
    Coordinator,
    CriticAgent,
    ExecutorAgent,
    MemoryAgent,
    PlannerAgent,
    ReviewerAgent,
)
from secondbrain.agent.coordination.models import KIND_MEMORY_STORE, AgentTask

from tests._coord_fakes import RISKY_STEPS, FakePlanner


def _coordinator(tmp_path, *, steps=None):
    agents = [PlannerAgent(planner=FakePlanner(steps)), CriticAgent(), ReviewerAgent(), ExecutorAgent(),
              MemoryAgent()]
    return Coordinator(tmp_path, agents=agents, with_goals=False)


def test_capabilities_map_covers_specialists(tmp_path):
    c = Coordinator(tmp_path, with_goals=False)
    caps = c.capabilities()
    for kind in ("plan", "execute", "review", "critique", "search", "import.check",
                 "memory.store", "memory.recall"):
        assert kind in caps


def test_delegate_routes_by_capability(tmp_path):
    c = _coordinator(tmp_path)
    res = c.delegate(AgentTask.create(KIND_MEMORY_STORE, {"text": "Fakt"}))
    assert res.ok
    assert res.agent == "memory"


def test_delegate_unknown_kind_fails(tmp_path):
    c = _coordinator(tmp_path)
    res = c.delegate(AgentTask.create("does.not.exist", {}))
    assert res.ok is False
    assert "no_agent_for_kind" in res.error


def test_solve_full_pipeline_executes(tmp_path):
    c = _coordinator(tmp_path)  # clean low-risk plan
    out = c.solve("Importiere die Prozessdokumente")
    assert out["ok"] is True
    assert out["approved"] is True
    assert out["executed"] is True
    assert out["execution"]["state"] == "COMPLETED"


def test_solve_blocks_execution_on_high_severity(tmp_path):
    c = _coordinator(tmp_path, steps=RISKY_STEPS)
    out = c.solve("Loesche alte Daten")
    assert out["critique"]["severity"] == "high"
    assert out["executed"] is False
    assert out["execution"] is None


def test_solve_populates_shared_context(tmp_path):
    c = _coordinator(tmp_path)
    c.solve("Ziel")
    ctx = c.context()
    assert ctx.get("plan") is not None
    assert ctx.get("critique") is not None
    assert ctx.get("review") is not None
    assert ctx.get("solution")["ok"] is True


def test_bus_records_delegation_messages(tmp_path):
    c = _coordinator(tmp_path)
    c.solve("Ziel")
    # each delegate publishes a task: and a result message
    topics = {m.topic for m in c.bus.log}
    assert "result" in topics
    assert any(t.startswith("task:") for t in topics)


def test_shared_memory_is_shared_across_agents(tmp_path):
    c = _coordinator(tmp_path)
    c.delegate(AgentTask.create(KIND_MEMORY_STORE, {"text": "Gemeinsame Erinnerung"}))
    # a second delegation recalls what the first stored -> shared memory
    from secondbrain.agent.coordination.models import KIND_MEMORY_RECALL
    res = c.delegate(AgentTask.create(KIND_MEMORY_RECALL, {"query": "Gemeinsame"}))
    assert res.output["count"] >= 1
