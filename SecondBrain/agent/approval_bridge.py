from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from secondbrain.native.approval import NativeApprovalQueue, ReviewQueue

from .task_planner import TaskStepState
from .tool_registry import ToolDefinition


class AgentApprovalBridge:
    """Persist blocked agent steps in the shared native approval queue."""

    def __init__(
        self,
        project_root: str | Path | None = None,
        *,
        queue: NativeApprovalQueue | None = None,
        review_queue: ReviewQueue | None = None,
    ) -> None:
        self.queue = queue or NativeApprovalQueue(project_root or Path.cwd())
        self.review_queue = review_queue or ReviewQueue(self.queue.project_root)
        if self.review_queue.project_root != self.queue.project_root:
            raise ValueError("review_approval_root_mismatch")

    def create_approval(
        self,
        *,
        plan_id: str,
        step_id: str,
        tool: ToolDefinition,
        intent: str,
        payload: Mapping[str, Any],
        workspace_id: str | None = None,
        create_review: bool = False,
        review_title: str = "",
        review_description: str = "",
        review_source: str = "agent",
        review_category: str | None = None,
    ) -> dict[str, Any]:
        category = self.category_for(tool.name, intent=intent, tool_category=tool.category)
        safe_payload = tool.input_schema.sanitize(payload)
        approval = self.queue.create(
            command=tool.name,
            intent=intent,
            text=f"Agent step requires approval: {tool.name}",
            target=step_id,
            risk_level=tool.risk_level.value,
            reason="Agent tool execution requires explicit approval.",
            category=category,
            plan_id=plan_id,
            step_id=step_id,
            tool_name=tool.name,
            payload=safe_payload,
            workspace_id=workspace_id,
            step_state=TaskStepState.WAITING_FOR_APPROVAL.value,
        )
        if not create_review:
            return approval
        review = self.review_queue.create(
            category=review_category or category,
            title=review_title or f"Review required: {tool.name}",
            description=review_description or str(approval.get("reason") or ""),
            source=review_source,
            target=step_id,
            approval_id=str(approval["approval_id"]),
            metadata={
                "risk_level": tool.risk_level.value,
                "plan_id": plan_id,
                "step_id": step_id,
                "tool_name": tool.name,
                "workspace_id": workspace_id,
            },
        )
        return self.queue.link_review(str(approval["approval_id"]), str(review["review_id"]))

    @staticmethod
    def category_for(tool_name: str, *, intent: str = "", tool_category: str = "") -> str:
        action = f"{tool_name} {intent} {tool_category}".lower()
        if any(token in action for token in ("delete", "remove", "trash")):
            return "delete_request"
        if any(token in action for token in ("permission", "scope", "oauth", "role", "access")):
            return "connector_permission_change"
        return "risky_agent_action"

    @staticmethod
    def step_state_for_status(status: str) -> TaskStepState:
        states = {
            "approved": TaskStepState.APPROVED,
            "rejected": TaskStepState.REJECTED,
            "deferred": TaskStepState.DEFERRED,
        }
        try:
            return states[status]
        except KeyError as exc:
            raise ValueError(f"unsupported_approval_status:{status}") from exc
