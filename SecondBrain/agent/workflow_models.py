"""v30.3 - workflow domain models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class WorkflowStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True)
class WorkflowStep:
    id: str
    name: str
    tool_name: str | None = None
    input: dict[str, Any] = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)
    timeout_seconds: int = 300
    max_retries: int = 3
    requires_approval: bool = False


@dataclass(frozen=True)
class WorkflowPlan:
    id: str
    objective: str
    steps: list[WorkflowStep]
