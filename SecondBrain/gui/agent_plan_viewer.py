from __future__ import annotations

from typing import Any


class AgentPlanViewer:
    """UI-free view model for planner details, explain output and audit trail."""

    def render(self, plan: dict[str, Any], *, explanation: dict[str, Any] | None = None) -> dict[str, Any]:
        steps = [dict(item) for item in plan.get("steps") or []]
        by_status: dict[str, int] = {}
        by_risk: dict[str, int] = {}
        for step in steps:
            status = str(step.get("status") or "pending")
            by_status[status] = by_status.get(status, 0) + 1
            risk = str(step.get("risk_level") or "low")
            by_risk[risk] = by_risk.get(risk, 0) + 1

        model = {
            "plan_id": str(plan.get("id") or ""),
            "goal": str(plan.get("goal") or ""),
            "status": str(plan.get("status") or "unknown"),
            "summary": {
                "steps": len(steps),
                "by_status": by_status,
                "by_risk": by_risk,
                "approval_gates": sum(1 for step in steps if bool(step.get("requires_approval"))),
            },
            "steps": steps,
        }
        if explanation:
            model["explain"] = {
                "maximum_risk": explanation.get("maximum_risk", "low"),
                "dependencies": dict(explanation.get("dependencies") or {}),
                "approval_gates": list(explanation.get("approval_gates") or []),
                "risky_steps": list(explanation.get("risky_steps") or []),
                "tool_mapping": dict(explanation.get("tool_mapping") or {}),
                "audit": list(explanation.get("audit") or []),
            }
        return model
