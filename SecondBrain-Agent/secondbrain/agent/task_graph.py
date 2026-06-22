"""P2 v21.0 - Task Graph Foundation."""

from dataclasses import dataclass, field


@dataclass
class TaskNode:
    task_id: str
    description: str
    dependencies: list[str] = field(default_factory=list)


class TaskGraph:
    def __init__(self):
        self._tasks: dict[str, TaskNode] = {}

    def add(self, task: TaskNode):
        self._tasks[task.task_id] = task

    def get(self, task_id: str):
        return self._tasks.get(task_id)

    def list(self):
        return list(self._tasks.values())
