"""Data model for integrated task & project management.

One shared model used by the agent, connectors and the user. Statuses and
priorities are constrained enums; dependencies carry a type and lag; every
mutation emits a :class:`TaskEvent` for an auditable trail.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4

__all__ = [
    "Status", "Priority", "DependencyType", "TaskEventType",
    "Project", "Task", "TaskDependency", "TaskEvent",
    "VALID_TASK_TRANSITIONS", "new_id", "utc_now",
]


class Status(StrEnum):
    INBOX = "inbox"
    PLANNED = "planned"
    ACTIVE = "active"
    BLOCKED = "blocked"
    WAITING = "waiting"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class Priority(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class DependencyType(StrEnum):
    FINISH_TO_START = "finish_to_start"
    START_TO_START = "start_to_start"
    FINISH_TO_FINISH = "finish_to_finish"
    START_TO_FINISH = "start_to_finish"


class TaskEventType(StrEnum):
    CREATED = "created"
    UPDATED = "updated"
    COMPLETED = "completed"
    REOPENED = "reopened"
    DEFERRED = "deferred"
    BLOCKED = "blocked"
    DELETED = "deleted"


# Allowed status transitions (open -> ... -> terminal). Terminal states can be
# reopened to active or archived.
VALID_TASK_TRANSITIONS: dict[Status, frozenset[Status]] = {
    Status.INBOX: frozenset({Status.PLANNED, Status.ACTIVE, Status.BLOCKED, Status.WAITING, Status.COMPLETED, Status.CANCELLED, Status.ARCHIVED}),
    Status.PLANNED: frozenset({Status.ACTIVE, Status.BLOCKED, Status.WAITING, Status.COMPLETED, Status.CANCELLED, Status.ARCHIVED, Status.INBOX}),
    Status.ACTIVE: frozenset({Status.BLOCKED, Status.WAITING, Status.COMPLETED, Status.CANCELLED, Status.PLANNED}),
    Status.BLOCKED: frozenset({Status.ACTIVE, Status.WAITING, Status.COMPLETED, Status.CANCELLED, Status.PLANNED}),
    Status.WAITING: frozenset({Status.ACTIVE, Status.BLOCKED, Status.COMPLETED, Status.CANCELLED, Status.PLANNED}),
    Status.COMPLETED: frozenset({Status.ACTIVE, Status.ARCHIVED}),
    Status.CANCELLED: frozenset({Status.ACTIVE, Status.ARCHIVED}),
    Status.ARCHIVED: frozenset({Status.ACTIVE}),
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:16]}"


@dataclass
class Project:
    project_id: str
    workspace_id: str
    title: str
    description: str = ""
    status: str = Status.PLANNED.value
    priority: str = Priority.NORMAL.value
    owner: str = ""
    start_date: str | None = None
    due_date: str | None = None
    progress: float = 0.0
    source: str = "user"
    source_reference: str = ""
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    archived_at: str | None = None
    version: int = 1

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Project":
        return cls(**{k: data.get(k) for k in cls.__dataclass_fields__ if k in data})


@dataclass
class Task:
    task_id: str
    project_id: str | None
    workspace_id: str
    title: str
    parent_task_id: str | None = None
    description: str = ""
    status: str = Status.INBOX.value
    priority: str = Priority.NORMAL.value
    due_date: str | None = None
    start_date: str | None = None
    completed_at: str | None = None
    assignee: str = ""
    estimated_minutes: int | None = None
    actual_minutes: int | None = None
    source: str = "user"
    source_reference: str = ""
    confidence: float = 1.0
    created_by: str = "user"
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    version: int = 1

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Task":
        return cls(**{k: data.get(k) for k in cls.__dataclass_fields__ if k in data})


@dataclass
class TaskDependency:
    predecessor_id: str
    successor_id: str
    dependency_id: str = field(default_factory=lambda: new_id("dep"))
    dependency_type: str = DependencyType.FINISH_TO_START.value
    lag_minutes: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TaskDependency":
        return cls(**{k: data.get(k) for k in cls.__dataclass_fields__ if k in data})


@dataclass
class TaskEvent:
    event_id: str
    task_id: str
    workspace_id: str
    event_type: str
    actor: str = "system"
    old_value: Any = None
    new_value: Any = None
    correlation_id: str = ""
    detail: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
