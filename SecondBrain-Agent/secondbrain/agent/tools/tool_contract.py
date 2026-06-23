from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Mapping


class ToolRisk(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ToolPermission(str, Enum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    EXECUTE = "execute"
    EXPORT = "export"


@dataclass(frozen=True)
class ToolParameter:
    name: str
    type_name: str
    required: bool = True
    default: Any | None = None
    description: str = ""
    sensitive: bool = False


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    parameters: tuple[ToolParameter, ...] = field(default_factory=tuple)
    permissions: tuple[ToolPermission, ...] = (ToolPermission.READ,)
    risk: ToolRisk = ToolRisk.LOW
    requires_approval: bool = False
    timeout_seconds: float = 30.0

    def parameter_map(self) -> dict[str, ToolParameter]:
        return {parameter.name: parameter for parameter in self.parameters}


@dataclass(frozen=True)
class ToolCall:
    tool_name: str
    arguments: Mapping[str, Any]
    caller: str = "agent"
    correlation_id: str | None = None


@dataclass(frozen=True)
class ToolResult:
    tool_name: str
    success: bool
    output: Any = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


ToolHandler = Callable[[Mapping[str, Any]], Any]
