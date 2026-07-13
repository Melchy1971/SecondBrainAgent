from __future__ import annotations

from secondbrain.gui.agent_plan_viewer import AgentPlanViewer


def test_agent_plan_viewer_renders_summary_and_explain():
    viewer = AgentPlanViewer()
    plan = {
        "id": "plan_1",
        "goal": "Goal",
        "status": "validated",
        "steps": [
            {"id": "s1", "status": "pending", "risk_level": "low", "requires_approval": False},
            {"id": "s2", "status": "waiting_approval", "risk_level": "high", "requires_approval": True},
        ],
    }
    explanation = {
        "maximum_risk": "high",
        "dependencies": {"s2": ["s1"]},
        "approval_gates": ["s2"],
        "risky_steps": ["s2"],
        "tool_mapping": {"s1": {"tool": "chat.ask"}},
        "audit": [{"event": "plan_created"}],
    }

    rendered = viewer.render(plan, explanation=explanation)

    assert rendered["summary"]["steps"] == 2
    assert rendered["summary"]["approval_gates"] == 1
    assert rendered["explain"]["dependencies"]["s2"] == ["s1"]
