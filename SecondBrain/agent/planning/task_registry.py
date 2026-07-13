from __future__ import annotations

from .task_graph import AgentTask


class TaskRegistry:
    def __init__(self) -> None:
        self._templates: dict[str, AgentTask] = {}

    def register(self, name: str, task: AgentTask) -> None:
        if not name.strip():
            raise ValueError("Task template name must not be empty")
        self._templates[name] = task

    def get(self, name: str) -> AgentTask:
        return self._templates[name]

    def list_names(self) -> list[str]:
        return sorted(self._templates)
