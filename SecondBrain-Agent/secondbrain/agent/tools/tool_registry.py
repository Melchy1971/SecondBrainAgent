"""Compatibility import for the canonical tool registry."""

from secondbrain.agent.tool_registry import ToolDefinition as RegisteredTool
from secondbrain.agent.tool_registry import ToolRegistry

__all__ = ["RegisteredTool", "ToolRegistry"]
