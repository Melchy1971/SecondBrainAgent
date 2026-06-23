from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .approval_manager import ApprovalManager
from .execution_context import ExecutionContext
from .planning_events import PlanningEventBus
from .task_graph import AgentTask, TaskGraph


@dataclass
class ExecutionResult:
    status: str
    completed_tasks: list[str] = field(default_factory=list)
    failed_tasks: list[str] = field(default_factory=list)
    waiting_approval: list[str] = field(default_factory=list)
    outputs: dict[str, Any] = field(default_factory=dict)


class ExecutionEngine:
    def __init__(
        self,
        approval_manager: ApprovalManager | None = None,
        event_bus: PlanningEventBus | None = None,
    ) -> None:
        self.approval_manager = approval_manager or ApprovalManager()
        self.event_bus = event_bus or PlanningEventBus()

    def execute(self, graph: TaskGraph, context: ExecutionContext | None = None) -> ExecutionResult:
        context = context or ExecutionContext()
        result = ExecutionResult(status="COMPLETED")
        self.event_bus.publish("PLAN_CREATED", {"tasks": len(graph.tasks)})

        for task in graph.topological():
            if any(graph.get(dep).status != "COMPLETED" for dep in task.dependencies):
                task.set_status("FAILED")
                result.failed_tasks.append(task.task_id)
                result.status = "FAILED"
                self.event_bus.publish("TASK_FAILED", {"task_id": task.task_id, "reason": "dependency_failed"})
                continue

            if self.approval_manager.requires_approval(task.tool_calls, task.metadata) and not self.approval_manager.granted_for(task.task_id):
                task.set_status("WAITING_APPROVAL")
                result.waiting_approval.append(task.task_id)
                result.status = "WAITING_APPROVAL"
                self.approval_manager.request(task.task_id, "Task requires approval", task.metadata)
                self.event_bus.publish("APPROVAL_REQUESTED", {"task_id": task.task_id})
                break

            try:
                self._execute_task(task, context, result)
            except Exception as exc:  # deterministic failure capture for UI/reporting
                task.set_status("FAILED")
                result.failed_tasks.append(task.task_id)
                result.status = "FAILED"
                result.outputs[task.task_id] = {"error": str(exc)}
                self.event_bus.publish("TASK_FAILED", {"task_id": task.task_id, "error": str(exc)})
                break

        return result

    def _execute_task(self, task: AgentTask, context: ExecutionContext, result: ExecutionResult) -> None:
        task.set_status("RUNNING")
        self.event_bus.publish("TASK_STARTED", {"task_id": task.task_id})
        outputs: list[dict[str, Any]] = []
        for tool_call in task.tool_calls:
            outputs.append(context.execute_tool(tool_call, {"task": task.to_dict()}))
        task.set_status("COMPLETED")
        result.completed_tasks.append(task.task_id)
        result.outputs[task.task_id] = outputs
        self.event_bus.publish("TASK_COMPLETED", {"task_id": task.task_id})
