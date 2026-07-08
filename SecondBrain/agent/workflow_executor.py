"""v30.3 - production workflow executor."""

from __future__ import annotations

from dataclasses import dataclass
from time import monotonic
from uuid import uuid4

from secondbrain.agent.dag_builder import DagBuilder
from secondbrain.agent.workflow_models import WorkflowPlan, WorkflowStatus


@dataclass(frozen=True)
class WorkflowExecutionResult:
    workflow_id: str
    status: str
    completed_steps: int
    failed_step: str | None = None
    error: str | None = None


class WorkflowExecutor:
    def __init__(self, tool_registry, repository=None, approval_system=None, retry_engine=None):
        self.tool_registry = tool_registry
        self.repository = repository
        self.approval_system = approval_system
        self.retry_engine = retry_engine
        self.dag = DagBuilder()

    def execute(self, plan: WorkflowPlan) -> WorkflowExecutionResult:
        ordered_steps = self.dag.topological_order(plan.steps)
        completed: set[str] = set()

        if self.repository:
            self.repository.save_plan(plan)
            self.repository.update_workflow_status(plan.id, WorkflowStatus.RUNNING.value)

        for step in ordered_steps:
            if any(dep not in completed for dep in step.dependencies):
                return self._fail(plan.id, step.id, "dependency not completed", len(completed))

            if step.requires_approval and self.approval_system and not self.approval_system.is_approved(step.id):
                if self.repository:
                    self.repository.update_workflow_status(plan.id, WorkflowStatus.WAITING_APPROVAL.value)
                    self.repository.update_step_status(step.id, WorkflowStatus.WAITING_APPROVAL.value)
                return WorkflowExecutionResult(plan.id, WorkflowStatus.WAITING_APPROVAL.value, len(completed))

            start = monotonic()
            attempt = 0
            while True:
                try:
                    tool = self.tool_registry.get(step.tool_name) if step.tool_name else None
                    if tool is None:
                        raise KeyError(f"unknown tool: {step.tool_name}")
                    output = tool(**step.input)
                    if monotonic() - start > step.timeout_seconds:
                        raise TimeoutError(f"step timeout: {step.id}")
                    if self.repository:
                        self.repository.update_step_status(step.id, WorkflowStatus.COMPLETED.value, output, attempt)
                        self.repository.record_event(str(uuid4()), plan.id, "STEP_COMPLETED", output, step.id)
                    completed.add(step.id)
                    break
                except Exception as exc:
                    attempt += 1
                    if attempt > step.max_retries:
                        return self._fail(plan.id, step.id, str(exc), len(completed), attempt)
                    if self.repository:
                        self.repository.record_event(
                            str(uuid4()), plan.id, "STEP_RETRY",
                            {"attempt": attempt, "error": str(exc)}, step.id,
                        )

        if self.repository:
            self.repository.update_workflow_status(plan.id, WorkflowStatus.COMPLETED.value)
        return WorkflowExecutionResult(plan.id, WorkflowStatus.COMPLETED.value, len(completed))

    def _fail(self, workflow_id: str, step_id: str, error: str, completed: int, attempt: int | None = None) -> WorkflowExecutionResult:
        if self.repository:
            self.repository.update_workflow_status(workflow_id, WorkflowStatus.FAILED.value)
            self.repository.update_step_status(step_id, WorkflowStatus.FAILED.value, {"error": error}, attempt)
            self.repository.record_event(str(uuid4()), workflow_id, "STEP_FAILED", {"error": error}, step_id)
        return WorkflowExecutionResult(workflow_id, WorkflowStatus.FAILED.value, completed, step_id, error)
