from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .approval_bridge import AgentApprovalBridge
from .approval_policy import MandatoryApprovalDecision
from .plan_store import AgentPlanStore
from .task_planner import TaskPlan, TaskStepState
from .tool_registry import ToolRegistry, ToolRegistryError, ToolRiskLevel


@dataclass(frozen=True)
class ExecutionResult:
    ok: bool
    plan_id: str
    results: list[Any]
    errors: list[str]
    status: str = "completed"
    approval_ids: list[str] = field(default_factory=list)
    waiting_step_ids: list[str] = field(default_factory=list)


class SafeExecutor:
    def __init__(
        self,
        registry: ToolRegistry,
        approval_bridge: AgentApprovalBridge | None = None,
        plan_store: AgentPlanStore | None = None,
    ) -> None:
        self.registry = registry
        self.approval_bridge = approval_bridge or AgentApprovalBridge()
        self.plan_store = plan_store
        self.registry.set_approval_lookup(self.approval_bridge.queue.get)

    def execute(
        self,
        plan: TaskPlan,
        *,
        confirmed: bool = False,
        workspace_id: str | None = None,
        approved_step_id: str | None = None,
    ) -> ExecutionResult:
        results: list[Any] = []
        errors: list[str] = []
        approval_ids: list[str] = []
        waiting_step_ids: list[str] = []
        status = ""
        for step in plan.steps:
            if step.state in {TaskStepState.COMPLETED, TaskStepState.SKIPPED}:
                continue
            if step.state == TaskStepState.REJECTED:
                status = "rejected"
                break
            if step.state == TaskStepState.FAILED:
                status = "failed"
                if step.error:
                    errors.append(step.error)
                break
            if step.state == TaskStepState.RUNNING:
                status = "execution_in_progress"
                break

            is_approved_step = step.step_id == approved_step_id
            if step.state in {
                TaskStepState.WAITING_FOR_APPROVAL,
                TaskStepState.APPROVED,
                TaskStepState.DEFERRED,
            } and not is_approved_step:
                approval = self._approval_for_step(plan.plan_id, step.step_id)
                if approval is not None:
                    approval_ids.append(str(approval["approval_id"]))
                waiting_step_ids.append(step.step_id)
                status = "waiting_for_approval"
                break

            if not step.tool_name:
                step.state = TaskStepState.RUNNING
                self._persist(plan, "running")
                step.result = {"type": "chat", "text": step.payload.get("text", "")}
                step.state = TaskStepState.COMPLETED
                results.append(step.result)
                continue
            try:
                definition = self.registry.get(step.tool_name)
                policy = self.registry.approval_policy.evaluate_tool(definition)
                if policy.effective_requires_approval and not is_approved_step:
                    approval = self.approval_bridge.create_approval(
                        plan_id=plan.plan_id,
                        step_id=step.step_id,
                        tool=definition,
                        intent=plan.intent,
                        payload=step.payload,
                        workspace_id=workspace_id,
                    )
                    approval = self._enrich_approval(approval, policy)
                    approval_id = str(approval["approval_id"])
                    step.result = {
                        "status": "waiting_for_approval",
                        "approval_id": approval_id,
                    }
                    step.state = TaskStepState.WAITING_FOR_APPROVAL
                    approval_ids.append(approval_id)
                    waiting_step_ids.append(step.step_id)
                    status = "waiting_for_approval"
                    break

                step.state = TaskStepState.RUNNING
                self._persist(plan, "running")
                approval_evidence = self._approval_for_step(plan.plan_id, step.step_id) if is_approved_step else None
                step.result = self.registry.execute(
                    step.tool_name,
                    step.payload,
                    confirmed=confirmed,
                    approval=approval_evidence,
                )
                step.state = TaskStepState.COMPLETED
                results.append(step.result)
                if is_approved_step:
                    approval = self._approval_for_step(plan.plan_id, step.step_id)
                    if approval is not None and approval.get("status") == "approved":
                        self.approval_bridge.queue.transition(
                            str(approval["approval_id"]),
                            "executed",
                            actor="agent_executor",
                            note="Approved agent step executed.",
                            step_state=TaskStepState.COMPLETED.value,
                        )
            except (ToolRegistryError, Exception) as exc:  # noqa: BLE001 - isolate tool failures in agent boundary
                step.error = str(exc)
                step.state = TaskStepState.FAILED
                errors.append(str(exc))
                status = "failed"
                break

        if not status:
            status = "completed" if all(
                step.state in {TaskStepState.COMPLETED, TaskStepState.SKIPPED} for step in plan.steps
            ) else "pending"
        self._persist(plan, status, approval_ids=approval_ids)
        return ExecutionResult(
            ok=status == "completed",
            plan_id=plan.plan_id,
            results=results,
            errors=errors,
            status=status,
            approval_ids=approval_ids,
            waiting_step_ids=waiting_step_ids,
        )

    def resume_approved(self, approval_id: str) -> ExecutionResult:
        if self.plan_store is None:
            raise RuntimeError("agent_plan_store_not_configured")
        approval = self.approval_bridge.queue.get(approval_id)
        if approval is None:
            raise KeyError(f"approval_not_found:{approval_id}")
        plan_id = str(approval.get("plan_id") or "")
        step_id = str(approval.get("step_id") or "")
        if not plan_id or not step_id:
            raise ValueError(f"approval_missing_plan_step:{approval_id}")
        if not self.plan_store.claim_step(plan_id, step_id):
            return ExecutionResult(
                ok=False,
                plan_id=plan_id,
                results=[],
                errors=[],
                status="execution_in_progress",
            )
        try:
            approval = self.approval_bridge.queue.get(approval_id)
            if approval is None:
                raise KeyError(f"approval_not_found:{approval_id}")
            plan = self.plan_store.load(plan_id)
            step = next((item for item in plan.steps if item.step_id == step_id), None)
            if step is None:
                raise KeyError(f"approval_step_not_found:{approval_id}:{step_id}")

            if step.state == TaskStepState.COMPLETED or approval.get("status") == "executed":
                return self._existing_result(plan)
            if step.state == TaskStepState.RUNNING:
                return ExecutionResult(
                    ok=False,
                    plan_id=plan.plan_id,
                    results=[],
                    errors=[],
                    status="execution_in_progress",
                )
            if approval.get("status") != "approved":
                raise PermissionError(f"approval_not_approved:{approval_id}:{approval.get('status')}")
            return self.execute(
                plan,
                approved_step_id=step_id,
                workspace_id=str(approval.get("workspace_id")) if approval.get("workspace_id") else None,
            )
        finally:
            self.plan_store.release_step(plan_id, step_id)

    def _approval_for_step(self, plan_id: str, step_id: str) -> dict[str, Any] | None:
        for approval in reversed(self.approval_bridge.queue.list()):
            if approval.get("plan_id") == plan_id and approval.get("step_id") == step_id:
                return approval
        return None

    def _enrich_approval(
        self,
        approval: dict[str, Any],
        policy: MandatoryApprovalDecision,
    ) -> dict[str, Any]:
        enriched = {
            **approval,
            "category": policy.approval_category,
            "action_type": policy.action_type,
            **policy.audit_fields(),
        }
        queue = self.approval_bridge.queue
        rows = queue._read_all()  # noqa: SLF001 - NativeApprovalQueue has no metadata update API
        for index, row in enumerate(rows):
            if row.get("approval_id") == approval.get("approval_id"):
                rows[index] = enriched
                queue._write_all(rows)  # noqa: SLF001 - preserves the single native queue
                return enriched
        raise RuntimeError(f"approval_record_missing:{approval.get('approval_id')}")

    def _persist(self, plan: TaskPlan, status: str, *, approval_ids: list[str] | None = None) -> None:
        plan.metadata["status"] = status
        existing = {str(item) for item in plan.metadata.get("approval_ids", []) if item}
        existing.update(approval_ids or [])
        plan.metadata["approval_ids"] = sorted(existing)
        if self.plan_store is not None:
            self.plan_store.update(plan)

    @staticmethod
    def _existing_result(plan: TaskPlan) -> ExecutionResult:
        status = str(plan.metadata.get("status") or "completed")
        waiting = [
            step
            for step in plan.steps
            if step.state in {
                TaskStepState.WAITING_FOR_APPROVAL,
                TaskStepState.APPROVED,
                TaskStepState.DEFERRED,
            }
        ]
        approval_ids = [
            str(step.result["approval_id"])
            for step in waiting
            if isinstance(step.result, dict) and step.result.get("approval_id")
        ]
        return ExecutionResult(
            ok=status == "completed",
            plan_id=plan.plan_id,
            results=[],
            errors=[],
            status=status,
            approval_ids=approval_ids,
            waiting_step_ids=[step.step_id for step in waiting],
        )
