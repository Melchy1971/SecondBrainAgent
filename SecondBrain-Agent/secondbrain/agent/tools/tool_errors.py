from __future__ import annotations


class ToolError(Exception):
    """Base class for tool framework failures."""


class ToolNotFoundError(ToolError):
    pass


class ToolValidationError(ToolError):
    pass


class ToolPermissionError(ToolError):
    pass


class ToolApprovalRequired(ToolError):
    pass


class ToolExecutionError(ToolError):
    pass
