from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable


class FlowStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class FlowStep:
    step_id: str
    name: str
    action: Callable[[dict[str, Any]], Any]
    required: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.step_id.strip():
            raise ValueError("step_id must not be empty")
        if not self.name.strip():
            raise ValueError("name must not be empty")
        if not callable(self.action):
            raise TypeError("action must be callable")


@dataclass
class StepResult:
    step_id: str
    name: str
    status: FlowStatus
    output: Any = None
    error: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None


@dataclass
class FlowResult:
    flow_id: str
    status: FlowStatus
    steps: list[StepResult]
    context: dict[str, Any]
    started_at: datetime
    finished_at: datetime

    @property
    def passed(self) -> bool:
        return self.status == FlowStatus.PASSED

    @property
    def failed_steps(self) -> list[StepResult]:
        return [step for step in self.steps if step.status == FlowStatus.FAILED]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
