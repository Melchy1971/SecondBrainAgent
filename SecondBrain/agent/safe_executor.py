from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .review_queue import QueueStatus, ReviewApprovalQueue, ReviewCategory
from .task_planner import TaskPlan, TaskStepState
from .tool_registry import ToolRegistry, ToolRegistryError, ToolRiskLevel


@dataclass(frozen=True)
class ExecutionResult:
    ok: bool
    plan_id: str
    results: list[Any]
    errors: list[str]
    pending_approval_ids: list[str] = field(default_factory=list)


class SafeExecutor:
    def __init__(self, registry: ToolRegistry, approval_queue: ReviewApprovalQueue | None = None) -> None:
        self.registry = registry
        self.approval_queue = approval_queue

    def execute(self, plan: TaskPlan, *, confirmed: bool = False, workspace_id: str | None = None) -> ExecutionResult:
        results: list[Any] = []
        errors: list[str] = []
        pending: list[str] = []
        for step in plan.steps:
            step.state = TaskStepState.RUNNING
            if not step.tool_name:
                step.result = {"type": "chat", "text": step.payload.get("text", "")}
                step.state = TaskStepState.COMPLETED
                results.append(step.result)
                continue
            try:
                tool = self.registry.get(step.tool_name)
                requires_gate = tool.requires_approval or tool.risk_level in {ToolRiskLevel.HIGH, ToolRiskLevel.CRITICAL}
                if requires_gate and not confirmed:
                    if self.approval_queue is None:
                        raise PermissionError(f"approval_queue_required:{step.tool_name}")
                    item = self.approval_queue.create_approval(
                        category=_category_for_tool(step.tool_name, tool.category),
                        title=f"Freigabe erforderlich: {step.tool_name}",
                        reason=f"Tool-Risiko {tool.risk_level.value}; Ausführung wurde angehalten.",
                        plan_id=plan.plan_id,
                        step_id=step.step_id,
                        tool_name=step.tool_name,
                        payload=step.payload,
                        risk_level=tool.risk_level.value,
                        workspace_id=workspace_id,
                    )
                    step.result = {"status": QueueStatus.PENDING.value, "approval_id": item.item_id}
                    step.state = TaskStepState.WAITING_APPROVAL
                    pending.append(item.item_id)
                    break
                step.result = self.registry.execute(step.tool_name, step.payload, confirmed=confirmed)
                step.state = TaskStepState.COMPLETED
                results.append(step.result)
            except (ToolRegistryError, Exception) as exc:  # noqa: BLE001 - isolate tool failures in agent boundary
                step.error = str(exc)
                step.state = TaskStepState.FAILED
                errors.append(str(exc))
                break
        return ExecutionResult(ok=not errors and not pending, plan_id=plan.plan_id, results=results, errors=errors, pending_approval_ids=pending)

    def resume(self, approval_id: str) -> ExecutionResult:
        if self.approval_queue is None:
            raise RuntimeError("approval_queue_not_configured")
        item = self.approval_queue.get(approval_id)
        if item is None:
            raise KeyError(f"queue_item_not_found:{approval_id}")
        if item.get("status") != QueueStatus.APPROVED.value:
            raise PermissionError(f"approval_not_granted:{approval_id}:{item.get('status')}")
        tool_name = str(item.get("tool_name") or "")
        if not tool_name:
            raise ValueError(f"approval_missing_tool:{approval_id}")
        result = self.registry.execute(tool_name, dict(item.get("payload") or {}), confirmed=True)
        return ExecutionResult(ok=True, plan_id=str(item.get("plan_id") or ""), results=[result], errors=[])


def _category_for_tool(tool_name: str, category: str) -> ReviewCategory:
    normalized = f"{category}:{tool_name}".lower()
    if "delete" in normalized or "remove" in normalized or "trash" in normalized:
        return ReviewCategory.DELETE_REQUEST
    if "connector" in normalized and any(token in normalized for token in ("permission", "scope", "oauth")):
        return ReviewCategory.CONNECTOR_PERMISSION_CHANGE
    return ReviewCategory.RISKY_AGENT_ACTION
