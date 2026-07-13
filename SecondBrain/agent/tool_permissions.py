"""P2 v21.1 - Tool Permissions."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ToolPermission:
    tool_name: str
    allowed: bool = True


class ToolPermissionManager:
    def __init__(self):
        self._permissions: dict[str, ToolPermission] = {}

    def allow(self, tool_name: str):
        self._permissions[tool_name] = ToolPermission(tool_name, True)

    def deny(self, tool_name: str):
        self._permissions[tool_name] = ToolPermission(tool_name, False)

    def is_allowed(self, tool_name: str) -> bool:
        permission = self._permissions.get(tool_name)
        return True if permission is None else permission.allowed
