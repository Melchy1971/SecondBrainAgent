from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .task_planner import TaskPlan, TaskStepState
from .tool_registry import ToolRegistry, ToolRegistryError


@dataclass(frozen=True)
class ExecutionResult:
    ok: bool
    plan_id: str
    results: list[Any]
    errors: list[str]


class SafeExecutor:
    def __init__(self, registry: ToolRegistry) -> None:
        self.registry = registry

    def execute(self, plan: TaskPlan, *, confirmed: bool = False) -> ExecutionResult:
        results: list[Any] = []
        errors: list[str] = []
        executed_steps = []
        for step in plan.steps:
            step.state = TaskStepState.RUNNING
            if not step.tool_name:
                step.result = {"type": "chat", "text": step.payload.get("text", "")}
                step.state = TaskStepState.COMPLETED
                results.append(step.result)
                continue
            try:
                definition = self.registry.get(step.tool_name)
                step.tool_contract = {
                    "name": definition.name,
                    "category": definition.category,
                    "risk_level": definition.risk_level.value,
                    "requires_approval": definition.requires_approval,
                    "timeout_seconds": definition.timeout_seconds,
                    "retry_count": definition.retry_count,
                }
                run = self.registry.run(step.tool_name, step.payload, approved=confirmed)
                if not run.success:
                    raise ToolRegistryError(run.error or f"tool_execution_failed:{step.tool_name}")
                step.result = run.output
                step.state = TaskStepState.COMPLETED
                results.append(step.result)
                executed_steps.append(step)
            except (ToolRegistryError, Exception) as exc:  # noqa: BLE001 - isolate tool failures in agent boundary
                step.error = str(exc)
                step.state = TaskStepState.FAILED
                errors.append(str(exc))
                for completed in reversed(executed_steps):
                    if completed.tool_name:
                        rollback = self.registry.rollback(completed.tool_name, completed.payload, completed.result)
                        if not rollback.get("ok", False):
                            errors.append(str(rollback.get("error") or f"rollback_failed:{completed.tool_name}"))
                break
        return ExecutionResult(ok=not errors, plan_id=plan.plan_id, results=results, errors=errors)
