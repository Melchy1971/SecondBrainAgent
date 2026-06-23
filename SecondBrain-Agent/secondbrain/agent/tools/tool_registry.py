from __future__ import annotations

from dataclasses import dataclass, field

from .tool_contract import ToolDefinition, ToolHandler
from .tool_errors import ToolNotFoundError, ToolValidationError


@dataclass
class RegisteredTool:
    definition: ToolDefinition
    handler: ToolHandler


@dataclass
class ToolRegistry:
    _tools: dict[str, RegisteredTool] = field(default_factory=dict)

    def register(self, definition: ToolDefinition, handler: ToolHandler) -> None:
        if not definition.name or not definition.name.strip():
            raise ToolValidationError("tool name must not be empty")
        self._tools[definition.name] = RegisteredTool(definition=definition, handler=handler)

    def unregister(self, name: str) -> None:
        self._tools.pop(name, None)

    def get(self, name: str) -> RegisteredTool:
        try:
            return self._tools[name]
        except KeyError as exc:
            raise ToolNotFoundError(f"tool not registered: {name}") from exc

    def list_definitions(self) -> list[ToolDefinition]:
        return [tool.definition for tool in sorted(self._tools.values(), key=lambda item: item.definition.name)]

    def contains(self, name: str) -> bool:
        return name in self._tools
