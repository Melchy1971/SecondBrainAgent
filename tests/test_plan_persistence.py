from __future__ import annotations

import json

import pytest

from secondbrain.agent import AgentPlan, AgentStep, PlanPersistence, PlanStatus


def _plan(plan_id: str) -> AgentPlan:
    return AgentPlan(plan_id, "Goal", [AgentStep("step_1", "Title", "chat", "chat.ask", {"text": "Goal"}, "Answer")])


def test_plan_persistence_saves_loads_and_lists(tmp_path):
    store = PlanPersistence(tmp_path)
    first = store.save(_plan("plan_1"))
    second = store.save(_plan("plan_2"))

    assert store.load(first.id).goal == "Goal"
    assert {plan.id for plan in store.list()} == {first.id, second.id}
    payload = json.loads(store.path.read_text(encoding="utf-8"))
    assert set(payload) == {"plan_1", "plan_2"}


def test_plan_persistence_keeps_status_and_reports_missing_plan(tmp_path):
    store = PlanPersistence(tmp_path)
    plan = _plan("plan_1")
    plan.status = PlanStatus.CANCELLED
    store.save(plan)

    assert store.load(plan.id).status == PlanStatus.CANCELLED
    with pytest.raises(KeyError, match="agent_plan_not_found"):
        store.load("missing")
