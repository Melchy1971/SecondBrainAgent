"""Schema-validated settings for plugins."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from secondbrain.plugins.models import PluginManifest

_TYPES: dict[str, type | tuple[type, ...]] = {
    "string": str, "integer": int, "number": (int, float), "boolean": bool,
    "array": list, "object": dict,
}


class PluginSettings:
    def __init__(self, project_root: str | Path, manifest: PluginManifest) -> None:
        self.manifest = manifest
        self.path = Path(project_root).resolve() / "runtime" / "plugins" / "settings" / f"{manifest.id}.json"

    def load(self) -> dict[str, Any]:
        values = {
            key: spec["default"] for key, spec in self.manifest.settings_schema.items() if "default" in spec
        }
        if self.path.exists():
            try:
                payload = json.loads(self.path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise ValueError(f"plugin_settings_unreadable:{self.manifest.id}:{exc}") from exc
            if not isinstance(payload, dict):
                raise ValueError(f"plugin_settings_must_be_object:{self.manifest.id}")
            values.update(payload)
        self.validate(values)
        return values

    def get(self, key: str, default: Any = None) -> Any:
        return self.load().get(key, default)

    def set(self, key: str, value: Any) -> dict[str, Any]:
        if key not in self.manifest.settings_schema:
            raise ValueError(f"unknown_plugin_setting:{key}")
        values = self.load()
        values[key] = value
        self.validate(values)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(values, indent=2, ensure_ascii=False), encoding="utf-8")
        temporary.replace(self.path)
        return values

    def validate(self, values: Mapping[str, Any]) -> None:
        unknown = set(values) - set(self.manifest.settings_schema)
        if unknown:
            raise ValueError(f"unknown_plugin_setting:{','.join(sorted(unknown))}")
        for key, value in values.items():
            spec = self.manifest.settings_schema[key]
            expected_name = str(spec.get("type") or "string")
            expected = _TYPES[expected_name]
            numeric_boolean = expected_name in {"integer", "number"} and isinstance(value, bool)
            if numeric_boolean or not isinstance(value, expected):
                raise ValueError(f"invalid_plugin_setting_type:{key}:{expected_name}")
            if spec.get("secret") and (not isinstance(value, str) or not value.startswith("secret://")):
                raise ValueError(f"plugin_secret_reference_required:{key}")
