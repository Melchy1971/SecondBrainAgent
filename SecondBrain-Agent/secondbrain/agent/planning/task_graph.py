from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

VALID_TASK_STATES = {
    "CREATED",
    "PLANNED",
    "QUEUED",
    "RUNNING",
    "WAITING_APPROVAL",
    "COMPLETED",
    "FAILED",
    "CANCELLED",
    "REPLANNED",
}


@dataclass
class AgentTask:
    title: str
    description: str = ""
    dependencies: list[str] = field(default_factory=list)
    tool_calls: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    task_id: str = field(default_factory=lambda: str(uuid4()))
    status: str = "CREATED"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def set_status(self, status: str) -> None:
        if status not in VALID_TASK_STATES:
            raise ValueError(f"Invalid task status: {status}")
        self.status = status
        self.updated_at = datetime.now(timezone.utc)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "dependencies": list(self.dependencies),
            "tool_calls": list(self.tool_calls),
            "metadata": dict(self.metadata),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentTask":
        task = cls(
            task_id=data["task_id"],
            title=data["title"],
            description=data.get("description", ""),
            status=data.get("status", "CREATED"),
            dependencies=list(data.get("dependencies", [])),
            tool_calls=list(data.get("tool_calls", [])),
            metadata=dict(data.get("metadata", {})),
        )
        if data.get("created_at"):
            task.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            task.updated_at = datetime.fromisoformat(data["updated_at"])
        return task


class TaskGraph:
    def __init__(self, tasks: list[AgentTask] | None = None) -> None:
        self.tasks: dict[str, AgentTask] = {}
        for task in tasks or []:
            self.add(task)

    def add(self, task: AgentTask) -> AgentTask:
        if task.task_id in self.tasks:
            raise ValueError(f"Duplicate task id: {task.task_id}")
        self.tasks[task.task_id] = task
        self._validate_dependencies_exist()
        self._validate_acyclic()
        return task

    def get(self, task_id: str) -> AgentTask:
        return self.tasks[task_id]

    def ready(self) -> list[AgentTask]:
        return [
            task for task in self.tasks.values()
            if task.status in {"CREATED", "PLANNED", "QUEUED"}
            and all(self.tasks[dep].status == "COMPLETED" for dep in task.dependencies)
        ]

    def topological(self) -> list[AgentTask]:
        visited: set[str] = set()
        order: list[AgentTask] = []

        def visit(task_id: str) -> None:
            if task_id in visited:
                return
            for dep in self.tasks[task_id].dependencies:
                visit(dep)
            visited.add(task_id)
            order.append(self.tasks[task_id])

        for task_id in sorted(self.tasks):
            visit(task_id)
        return order

    def _validate_dependencies_exist(self) -> None:
        ids = set(self.tasks)
        for task in self.tasks.values():
            missing = set(task.dependencies) - ids
            if missing:
                raise ValueError(f"Missing dependencies for {task.task_id}: {sorted(missing)}")

    def _validate_acyclic(self) -> None:
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(task_id: str) -> None:
            if task_id in visiting:
                raise ValueError("Task graph contains a cycle")
            if task_id in visited:
                return
            visiting.add(task_id)
            for dep in self.tasks[task_id].dependencies:
                visit(dep)
            visiting.remove(task_id)
            visited.add(task_id)

        for task_id in self.tasks:
            visit(task_id)

    def to_dict(self) -> dict[str, Any]:
        return {"tasks": [task.to_dict() for task in self.topological()]}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TaskGraph":
        return cls([AgentTask.from_dict(item) for item in data.get("tasks", [])])
