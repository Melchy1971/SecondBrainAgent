"""Compatibility contract backed by the unified tool models."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Callable, Mapping

from secondbrain.agent.tool_registry import (
    ToolDefinition,
    ToolInputSchema,
    ToolResult,
    ToolRiskLevel,
)


ToolRisk = ToolRiskLevel


class ToolPermission(StrEnum):
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
class ToolCall:
    tool_name: str
    arguments: Mapping[str, Any]
    caller: str = "agent"
    correlation_id: str | None = None


ToolHandler = Callable[[Mapping[str, Any]], Any]

__all__ = [
    "ToolCall",
    "ToolDefinition",
    "ToolHandler",
    "ToolInputSchema",
    "ToolParameter",
    "ToolPermission",
    "ToolResult",
    "ToolRisk",
]
