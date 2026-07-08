"""Constrained API passed to activated plugins."""
from __future__ import annotations

from typing import Any, Callable, Mapping

from secondbrain.agent.tool_registry import ToolDefinition, ToolInputSchema, ToolRegistry, ToolRiskLevel
from secondbrain.plugins.models import PLUGIN_API_VERSION, PluginManifest
from secondbrain.plugins.permissions import PluginPermission, PluginPermissionPolicy
from secondbrain.plugins.sandbox import PluginSandbox
from secondbrain.plugins.settings import PluginSettings


class PluginAPI:
    version = PLUGIN_API_VERSION

    def __init__(self, manifest: PluginManifest, registry: ToolRegistry, sandbox: PluginSandbox,
                 settings: PluginSettings, policy: PluginPermissionPolicy) -> None:
        self.manifest = manifest
        self.registry = registry
        self.sandbox = sandbox
        self.settings = settings
        self.policy = policy
        self.registered_tools: list[str] = []

    @property
    def plugin_id(self) -> str:
        return self.manifest.id

    def info(self) -> dict[str, Any]:
        return {
            "plugin_id": self.plugin_id,
            "api_version": self.version,
            "permissions": self.policy.snapshot(),
            "capabilities": list(self.manifest.capabilities),
        }

    def get_setting(self, key: str, default: Any = None) -> Any:
        self.policy.require(PluginPermission.SETTINGS_READ, action=f"setting:get:{key}")
        return self.settings.get(key, default)

    def set_setting(self, key: str, value: Any) -> dict[str, Any]:
        self.policy.require(PluginPermission.SETTINGS_WRITE, action=f"setting:set:{key}")
        return self.settings.set(key, value)

    def read_text(self, path: str, *, max_chars: int = 1_000_000) -> str:
        return self.sandbox.read_text(path, max_chars=max_chars)

    def write_text(self, path: str, content: str):
        return self.sandbox.write_text(path, content)

    def register_tool(self, name: str, description: str, handler: Callable[[Mapping[str, Any]], Any], *,
                      input_schema: Mapping[str, Any] | ToolInputSchema | None = None,
                      output_schema: Mapping[str, Any] | None = None,
                      risk_level: ToolRiskLevel | str = ToolRiskLevel.LOW,
                      requires_approval: bool = False) -> ToolDefinition:
        self.policy.require(PluginPermission.TOOLS_REGISTER, action=f"tool:register:{name}")
        prefix = f"plugin.{self.plugin_id}."
        if not name.startswith(prefix):
            raise ValueError(f"plugin_tool_prefix_required:{prefix}")
        if not callable(handler):
            raise TypeError("plugin_tool_handler_not_callable")
        parsed_risk = ToolRiskLevel.parse(risk_level)
        definition = ToolDefinition(
            name,
            description,
            category=f"plugin:{self.plugin_id}",
            input_schema=ToolInputSchema.from_value(input_schema),
            output_schema=dict(output_schema or {"type": "object"}),
            risk_level=parsed_risk,
            requires_approval=requires_approval or parsed_risk in {ToolRiskLevel.HIGH, ToolRiskLevel.CRITICAL},
            handler=handler,
            metadata={"plugin_id": self.plugin_id, "plugin_version": self.manifest.version},
        )
        registered = self.registry.register(definition)
        self.registered_tools.append(registered.name)
        return registered
