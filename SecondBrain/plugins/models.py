"""v30.76 plugin manifest and runtime models."""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping

PLUGIN_API_VERSION = "1"
_PLUGIN_ID = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
_VERSION = re.compile(r"^\d+\.\d+\.\d+(?:[-+][A-Za-z0-9.-]+)?$")


class PluginManifestError(ValueError):
    pass


def _strings(value: Any, field_name: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, (list, tuple)):
        raise PluginManifestError(f"plugin_manifest_field_must_be_array:{field_name}")
    return tuple(str(item).strip() for item in value)


@dataclass(frozen=True, slots=True)
class PluginManifest:
    id: str
    name: str
    version: str
    description: str = ""
    api_version: str = PLUGIN_API_VERSION
    entrypoint: str = "plugin.py:register"
    permissions: tuple[str, ...] = ()
    capabilities: tuple[str, ...] = ()
    settings_schema: Mapping[str, Mapping[str, Any]] = field(default_factory=dict)
    marketplace: Mapping[str, Any] = field(default_factory=dict)
    enabled: bool = True

    def __post_init__(self) -> None:
        self.validate()

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "PluginManifest":
        try:
            manifest = cls(
                id=str(value["id"]).strip(),
                name=str(value["name"]).strip(),
                version=str(value["version"]).strip(),
                description=str(value.get("description") or "").strip(),
                api_version=str(value.get("api_version") or PLUGIN_API_VERSION).strip(),
                entrypoint=str(value.get("entrypoint") or "plugin.py:register").strip(),
                permissions=_strings(value.get("permissions"), "permissions"),
                capabilities=_strings(value.get("capabilities"), "capabilities"),
                settings_schema={str(key): dict(spec) for key, spec in dict(value.get("settings") or {}).items()},
                marketplace=dict(value.get("marketplace") or {}),
                enabled=value.get("enabled", True),
            )
        except PluginManifestError:
            raise
        except (KeyError, TypeError, ValueError) as exc:
            raise PluginManifestError(f"invalid_plugin_manifest:{exc}") from exc
        return manifest

    @classmethod
    def load(cls, path: str | Path) -> "PluginManifest":
        source = Path(path)
        try:
            if source.stat().st_size > 1_000_000:
                raise PluginManifestError(f"plugin_manifest_too_large:{source}")
            payload = json.loads(source.read_text(encoding="utf-8"))
        except PluginManifestError:
            raise
        except (OSError, json.JSONDecodeError) as exc:
            raise PluginManifestError(f"plugin_manifest_unreadable:{source}:{exc}") from exc
        if not isinstance(payload, dict):
            raise PluginManifestError("plugin_manifest_must_be_object")
        return cls.from_dict(payload)

    def validate(self) -> None:
        if not _PLUGIN_ID.fullmatch(self.id):
            raise PluginManifestError(f"invalid_plugin_id:{self.id}")
        if not self.name:
            raise PluginManifestError("plugin_name_required")
        if not _VERSION.fullmatch(self.version):
            raise PluginManifestError(f"invalid_plugin_version:{self.version}")
        if self.api_version != PLUGIN_API_VERSION:
            raise PluginManifestError(f"unsupported_plugin_api:{self.api_version}")
        module, separator, callable_name = self.entrypoint.partition(":")
        module_path = Path(module)
        if not separator or not callable_name.isidentifier() or module_path.is_absolute() or module_path.suffix != ".py":
            raise PluginManifestError(f"invalid_plugin_entrypoint:{self.entrypoint}")
        if ".." in module_path.parts:
            raise PluginManifestError("plugin_entrypoint_path_traversal")
        if len(set(self.permissions)) != len(self.permissions):
            raise PluginManifestError("duplicate_plugin_permission")
        if not isinstance(self.enabled, bool):
            raise PluginManifestError("plugin_enabled_must_be_boolean")
        from secondbrain.plugins.permissions import PluginPermission
        for permission in self.permissions:
            try:
                PluginPermission.parse(permission)
            except ValueError as exc:
                raise PluginManifestError(str(exc)) from exc
        allowed_types = {"string", "integer", "number", "boolean", "array", "object"}
        for key, spec in self.settings_schema.items():
            if not key or not isinstance(spec, dict) or spec.get("type", "string") not in allowed_types:
                raise PluginManifestError(f"invalid_plugin_setting:{key}")

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["permissions"] = list(self.permissions)
        data["capabilities"] = list(self.capabilities)
        data["settings"] = data.pop("settings_schema")
        return data


@dataclass(slots=True)
class LoadedPlugin:
    manifest: PluginManifest
    root: Path
    status: str = "discovered"
    error: str = ""
    module_name: str = ""
    registered_tools: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.manifest.id,
            "name": self.manifest.name,
            "version": self.manifest.version,
            "root": str(self.root),
            "status": self.status,
            "error": self.error,
            "registered_tools": list(self.registered_tools),
            "permissions": list(self.manifest.permissions),
        }
