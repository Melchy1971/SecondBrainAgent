"""Permission policy for the constrained Plugin API."""
from __future__ import annotations

from enum import StrEnum
from typing import Iterable

from secondbrain.permissions_v106 import PermissionPolicy


class PluginPermission(StrEnum):
    WORKSPACE_READ = "workspace.read"
    WORKSPACE_WRITE = "workspace.write"
    SETTINGS_READ = "settings.read"
    SETTINGS_WRITE = "settings.write"
    TOOLS_REGISTER = "tools.register"
    NETWORK = "network"
    SHELL = "shell"
    SECRETS = "secrets"

    @classmethod
    def parse(cls, value: str | "PluginPermission") -> "PluginPermission":
        if isinstance(value, cls):
            return value
        try:
            return cls(str(value))
        except ValueError as exc:
            raise ValueError(f"unknown_plugin_permission:{value}") from exc

    @property
    def level(self) -> str:
        if self in {self.WORKSPACE_READ, self.SETTINGS_READ}:
            return "read"
        if self in {self.WORKSPACE_WRITE, self.SETTINGS_WRITE, self.TOOLS_REGISTER}:
            return "write"
        if self is self.NETWORK:
            return "execute"
        return "system"


class PluginPermissionPolicy:
    def __init__(self, plugin_id: str, *, declared: Iterable[str], granted: Iterable[str]) -> None:
        self.plugin_id = plugin_id
        self.declared = {PluginPermission.parse(item) for item in declared}
        self.granted = {PluginPermission.parse(item) for item in granted}
        max_level = max(({"read": 1, "write": 2, "execute": 3, "system": 4}[item.level] for item in self.granted), default=1)
        self.base = PermissionPolicy(max_level=max_level, require_approval_from_level=5)

    def require(self, permission: PluginPermission | str, *, action: str = "") -> None:
        wanted = PluginPermission.parse(permission)
        operation = action or wanted.value
        if wanted not in self.declared:
            raise PermissionError(f"plugin_permission_not_declared:{self.plugin_id}:{wanted.value}")
        if wanted not in self.granted:
            raise PermissionError(f"plugin_permission_not_granted:{self.plugin_id}:{wanted.value}")
        decision = self.base.evaluate(operation, wanted.level)
        if not decision.allowed:
            raise PermissionError(f"plugin_permission_denied:{self.plugin_id}:{wanted.value}:{decision.reason}")

    def snapshot(self) -> dict[str, list[str]]:
        return {
            "declared": sorted(item.value for item in self.declared),
            "granted": sorted(item.value for item in self.granted),
        }
