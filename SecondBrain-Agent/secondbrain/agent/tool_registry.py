from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


class ToolRegistryError(ValueError):
    pass


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    handler: Callable[[dict[str, Any]], Any]
    category: str = "general"
    requires_confirmation: bool = False
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.name or not self.name.strip():
            raise ToolRegistryError("tool_name_required")
        if not callable(self.handler):
            raise ToolRegistryError("tool_handler_not_callable")

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Compatibility call path for the original positional tool API."""
        return self.handler(*args, **kwargs)


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition | str, handler: Callable[..., Any] | None = None) -> ToolDefinition:
        if isinstance(tool, str):
            if handler is None:
                raise ToolRegistryError("tool_handler_not_callable")
            tool = ToolDefinition(name=tool, description=tool, handler=handler)
        tool.validate()
        if tool.name in self._tools:
            raise ToolRegistryError(f"tool_already_registered:{tool.name}")
        self._tools[tool.name] = tool
        return tool

    def get(self, name: str) -> ToolDefinition:
        try:
            return self._tools[name]
        except KeyError as exc:
            raise ToolRegistryError(f"tool_not_found:{name}") from exc

    def has(self, name: str) -> bool:
        return name in self._tools

    def list(self, *, enabled_only: bool = True) -> list[ToolDefinition]:
        tools = list(self._tools.values())
        if enabled_only:
            tools = [tool for tool in tools if tool.enabled]
        return sorted(tools, key=lambda tool: (tool.category, tool.name))

    def execute(self, name: str, payload: dict[str, Any] | None = None, *, confirmed: bool = False) -> Any:
        tool = self.get(name)
        if not tool.enabled:
            raise ToolRegistryError(f"tool_disabled:{name}")
        if tool.requires_confirmation and not confirmed:
            raise ToolRegistryError(f"tool_requires_confirmation:{name}")
        return tool.handler(payload or {})
