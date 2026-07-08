from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

ToolHandler = Callable[[dict[str, Any]], dict[str, Any]]


@dataclass
class ExecutionContext:
    workspace_id: str | None = None
    user_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    tool_handlers: dict[str, ToolHandler] = field(default_factory=dict)

    def register_tool(self, name: str, handler: ToolHandler) -> None:
        self.tool_handlers[name] = handler

    def execute_tool(self, name: str, payload: dict[str, Any]) -> dict[str, Any]:
        if name not in self.tool_handlers:
            raise KeyError(f"Tool handler not registered: {name}")
        return self.tool_handlers[name](payload)
