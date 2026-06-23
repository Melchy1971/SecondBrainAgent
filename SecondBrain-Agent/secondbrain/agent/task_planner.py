from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any
from uuid import uuid4


class TaskStepState(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class TaskStep:
    step_id: str
    name: str
    tool_name: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    state: TaskStepState = TaskStepState.PENDING
    result: Any = None
    error: str | None = None


@dataclass
class TaskPlan:
    plan_id: str
    intent: str
    steps: list[TaskStep]
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_executable(self) -> bool:
        return bool(self.steps) and all(step.state == TaskStepState.PENDING for step in self.steps)


class TaskPlanner:
    def create_single_tool_plan(self, *, intent: str, tool_name: str, payload: dict[str, Any] | None = None) -> TaskPlan:
        return TaskPlan(
            plan_id=str(uuid4()),
            intent=intent,
            steps=[TaskStep(step_id=str(uuid4()), name=intent, tool_name=tool_name, payload=payload or {})],
        )

    def create_chat_plan(self, *, text: str) -> TaskPlan:
        return TaskPlan(
            plan_id=str(uuid4()),
            intent="chat",
            steps=[TaskStep(step_id=str(uuid4()), name="respond", payload={"text": text})],
        )
