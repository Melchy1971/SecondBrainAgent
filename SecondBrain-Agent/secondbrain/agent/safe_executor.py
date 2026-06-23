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
        for step in plan.steps:
            step.state = TaskStepState.RUNNING
            if not step.tool_name:
                step.result = {"type": "chat", "text": step.payload.get("text", "")}
                step.state = TaskStepState.COMPLETED
                results.append(step.result)
                continue
            try:
                step.result = self.registry.execute(step.tool_name, step.payload, confirmed=confirmed)
                step.state = TaskStepState.COMPLETED
                results.append(step.result)
            except (ToolRegistryError, Exception) as exc:  # noqa: BLE001 - isolate tool failures in agent boundary
                step.error = str(exc)
                step.state = TaskStepState.FAILED
                errors.append(str(exc))
                break
        return ExecutionResult(ok=not errors, plan_id=plan.plan_id, results=results, errors=errors)
