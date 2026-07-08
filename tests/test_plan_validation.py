from __future__ import annotations

import pytest

from secondbrain.agent import AgentPlan, AgentStep, PlanStatus, PlanValidator


def test_plan_validation_accepts_complete_contract():
    plan = AgentPlan(
        id="plan_1",
        goal="Diagnose",
        steps=[AgentStep("step_1", "Status", "diagnostics", "command.center", {"command": "system.status"}, "Status payload")],
    )
    assert PlanValidator().validate(plan) == []


def test_plan_validation_rejects_duplicate_ids_and_unsafe_risk():
    plan = AgentPlan(
        id="plan_1",
        goal="Riskant",
        steps=[
            AgentStep("same", "A", "write", "tool", {}, "A", risk_level="high", requires_approval=False),
            AgentStep("same", "B", "read", "tool", {}, "B", status=PlanStatus.PENDING),
        ],
    )
    errors = PlanValidator().validate(plan)
    assert "step[1].duplicate_id:same" in errors
    assert "step[0].approval_required_for_risk" in errors
    with pytest.raises(ValueError, match="invalid_agent_plan"):
        PlanValidator().require_valid(plan)
