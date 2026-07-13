"""Discovery and explicitly trusted activation of local plugins."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Iterable, Mapping

from secondbrain.agent.tool_registry import ToolRegistry
from secondbrain.plugins.api import PluginAPI
from secondbrain.plugins.models import LoadedPlugin, PluginManifest, PluginManifestError
from secondbrain.plugins.permissions import PluginPermissionPolicy
from secondbrain.plugins.sandbox import PluginSandbox
from secondbrain.plugins.settings import PluginSettings


class PluginLoader:
    MANIFEST_NAME = "plugin.json"

    def __init__(self, project_root: str | Path = ".", *, plugin_roots: Iterable[str | Path] | None = None,
                 tool_registry: ToolRegistry | None = None,
                 grants: Mapping[str, Iterable[str]] | None = None,
                 trusted_plugins: Iterable[str] = ()) -> None:
        self.project_root = Path(project_root).resolve()
        roots = tuple(plugin_roots or (self.project_root / "plugins",))
        self.plugin_roots = tuple(Path(root).resolve() for root in roots)
        self.tool_registry = tool_registry
        self.grants = {str(key): tuple(value) for key, value in dict(grants or {}).items()}
        self.trusted_plugins = {str(item) for item in trusted_plugins}
        self.plugins: dict[str, LoadedPlugin] = {}
        self.errors: list[dict[str, str]] = []
        self._modules: dict[str, ModuleType] = {}

    def discover(self) -> list[LoadedPlugin]:
        if any(plugin.status == "active" for plugin in self.plugins.values()):
            raise RuntimeError("plugins_active_during_discovery")
        self.errors = []
        discovered: dict[str, LoadedPlugin] = {}
        for root in self.plugin_roots:
            if not root.is_dir():
                continue
            for manifest_path in sorted(root.glob(f"*/{self.MANIFEST_NAME}")):
                try:
                    plugin_root = manifest_path.parent.resolve()
                    if not plugin_root.is_relative_to(root):
                        raise PluginManifestError("plugin_directory_outside_discovery_root")
                    manifest = PluginManifest.load(manifest_path)
                    if manifest.id in discovered:
                        raise PluginManifestError(f"duplicate_plugin_id:{manifest.id}")
                    discovered[manifest.id] = LoadedPlugin(manifest, plugin_root)
                except PluginManifestError as exc:
                    self.errors.append({"path": str(manifest_path), "error": str(exc)})
        self.plugins = discovered
        return list(discovered.values())

    def list(self) -> list[dict]:
        return [plugin.to_dict() for plugin in sorted(self.plugins.values(), key=lambda item: item.manifest.id)]

    def get(self, plugin_id: str) -> LoadedPlugin:
        try:
            return self.plugins[plugin_id]
        except KeyError as exc:
            raise KeyError(f"plugin_not_found:{plugin_id}") from exc

    def activate(self, plugin_id: str) -> LoadedPlugin:
        plugin = self.get(plugin_id)
        if plugin.status == "active":
            return plugin
        if not plugin.manifest.enabled:
            raise PermissionError(f"plugin_disabled:{plugin_id}")
        if plugin_id not in self.trusted_plugins:
            raise PermissionError(f"plugin_not_trusted:{plugin_id}")
        module_path, _, callable_name = plugin.manifest.entrypoint.partition(":")
        policy = PluginPermissionPolicy(
            plugin_id, declared=plugin.manifest.permissions, granted=self.grants.get(plugin_id, ()),
        )
        sandbox = PluginSandbox(self.project_root, plugin.root, plugin_id, policy)
        entrypoint = sandbox.resolve_entrypoint(module_path)
        module_name = f"secondbrain_plugin_{plugin_id.replace('.', '_').replace('-', '_')}"
        registry = self.tool_registry or ToolRegistry(self.project_root / "runtime")
        self.tool_registry = registry
        api: PluginAPI | None = None
        try:
            module = self._import(module_name, entrypoint)
            register = getattr(module, callable_name, None)
            if not callable(register):
                raise PluginManifestError(f"plugin_entrypoint_callable_missing:{plugin.manifest.entrypoint}")
            api = PluginAPI(plugin.manifest, registry, sandbox, PluginSettings(self.project_root, plugin.manifest), policy)
            register(api)
        except Exception as exc:
            for tool_name in reversed(api.registered_tools if api is not None else ()):
                registry.unregister(tool_name)
            sys.modules.pop(module_name, None)
            plugin.status, plugin.error = "error", f"{type(exc).__name__}: {exc}"
            raise
        plugin.status = "active"
        plugin.error = ""
        plugin.module_name = module_name
        plugin.registered_tools = tuple(api.registered_tools)
        self._modules[plugin_id] = module
        return plugin

    def deactivate(self, plugin_id: str) -> LoadedPlugin:
        plugin = self.get(plugin_id)
        module = self._modules.get(plugin_id)
        shutdown = getattr(module, "shutdown", None) if module is not None else None
        shutdown_error = ""
        if callable(shutdown):
            try:
                shutdown()
            except Exception as exc:  # cleanup must continue
                shutdown_error = f"{type(exc).__name__}: {exc}"
        if self.tool_registry is not None:
            for tool_name in plugin.registered_tools:
                self.tool_registry.unregister(tool_name)
        if plugin.module_name:
            sys.modules.pop(plugin.module_name, None)
        self._modules.pop(plugin_id, None)
        plugin.status, plugin.module_name, plugin.registered_tools = "inactive", "", ()
        plugin.error = shutdown_error
        return plugin

    @staticmethod
    def _import(module_name: str, path: Path) -> ModuleType:
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"plugin_import_spec_failed:{path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
        except Exception:
            sys.modules.pop(module_name, None)
            raise
        return module
