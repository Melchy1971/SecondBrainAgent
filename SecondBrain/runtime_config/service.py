"""Zentrale RuntimeConfig: Auflösung, Validierung, BLOCKED-Status, Schreiben.

GUI und CLI nutzen ausschließlich diese Klasse; siehe Paket-Docstring für die
Prioritätenkette.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Mapping

from secondbrain.install.app_home import resolve_home
from secondbrain.runtime_config.schema import CONFIG_KEYS, KEYS_BY_NAME, SECTIONS, ConfigKey
from secondbrain.runtime_config.sources import (
    PRECEDENCE, SOURCE_APPDATA, SOURCE_DEFAULT, SOURCE_DOTENV, SOURCE_ENV,
    SOURCE_GUI_LEGACY, SOURCE_WORKSPACE,
    read_dotenv, read_json_config, write_dotenv, write_json_config,
)

SCHEMA = "secondbrain.runtime_config.v1"
SECRET_MASK = "••••••••"
STATUS_OK = "ok"
STATUS_BLOCKED = "blocked"


class RuntimeConfig:
    def __init__(
        self,
        project_root: str | Path | None = None,
        env: Mapping[str, str] | None = None,
        home: str | Path | None = None,
    ):
        self.project_root = Path(project_root or Path.cwd()).resolve()
        self._env: Mapping[str, str] = os.environ if env is None else env
        self.home = Path(home) if home is not None else resolve_home(self._env)
        self.dotenv_path = self.project_root / ".env"
        self.workspace_config_path = self.project_root / "config.json"
        self.appdata_config_path = self.home / "config" / "config.json"
        self.gui_legacy_path = self.project_root / "runtime" / "gui" / "settings.json"

    # -- Quellen ---------------------------------------------------------
    def _load_sources(self) -> tuple[dict[str, dict[str, str]], list[str]]:
        issues: list[str] = []
        workspace, ws_issues = read_json_config(self.workspace_config_path)
        appdata, ad_issues = read_json_config(self.appdata_config_path)
        gui_legacy, gui_issues = read_json_config(self.gui_legacy_path)
        issues.extend(ws_issues + ad_issues + gui_issues)
        sources = {
            SOURCE_ENV: {k: str(v) for k, v in self._env.items()},
            SOURCE_DOTENV: read_dotenv(self.dotenv_path),
            SOURCE_WORKSPACE: workspace,
            SOURCE_APPDATA: appdata,
            SOURCE_GUI_LEGACY: gui_legacy,
            SOURCE_DEFAULT: {key.key: key.default for key in CONFIG_KEYS},
        }
        return sources, issues

    def _secret_ref(self, spec: ConfigKey, sources: dict[str, dict[str, str]]) -> str:
        ref_key = f"{spec.key}::ref"
        for name in (SOURCE_WORKSPACE, SOURCE_APPDATA):
            if ref_key in sources[name]:
                return sources[name][ref_key]
        return spec.key

    # -- Auflösung ---------------------------------------------------------
    def resolve(self) -> dict[str, Any]:
        """Effektive Werte + Herkunft je Key.

        Returns: {"values": {key: str}, "origins": {key: source}, "issues": [...]}.
        Secrets werden nur aus environ/.env aufgelöst (über ihre Referenz).
        """
        sources, issues = self._load_sources()
        values: dict[str, str] = {}
        origins: dict[str, str] = {}
        for spec in CONFIG_KEYS:
            if spec.secret:
                ref = self._secret_ref(spec, sources)
                for name in (SOURCE_ENV, SOURCE_DOTENV):
                    raw = sources[name].get(ref)
                    if raw is not None and raw != "":
                        values[spec.key] = raw
                        origins[spec.key] = name
                        break
                else:
                    values[spec.key] = spec.default
                    origins[spec.key] = SOURCE_DEFAULT
                continue
            for name in PRECEDENCE:
                raw = sources[name].get(spec.key)
                if raw is not None and raw != "":
                    values[spec.key] = raw
                    origins[spec.key] = name
                    break
            else:
                values[spec.key] = spec.default
                origins[spec.key] = SOURCE_DEFAULT
        return {"values": values, "origins": origins, "issues": issues}

    def get(self, key: str) -> str:
        KEYS_BY_NAME[key]  # KeyError bei unbekanntem Key
        return self.resolve()["values"][key]

    def path(self, key: str) -> Path:
        """Löst einen relpath-Key gegen den Workspace auf (absolute Werte bleiben)."""
        spec = KEYS_BY_NAME[key]
        if spec.type != "relpath":
            raise ValueError(f"{key} ist kein Pfad-Key")
        raw = Path(self.get(key))
        return raw if raw.is_absolute() else self.project_root / raw

    # -- Validierung -------------------------------------------------------
    def validate(self, values: Mapping[str, str] | None = None) -> list[dict[str, str]]:
        resolved = dict(self.resolve()["values"]) if values is None else dict(values)
        issues: list[dict[str, str]] = []

        def add(key: str, code: str, message: str, severity: str = "error") -> None:
            issues.append({"key": key, "code": code, "message": message, "severity": severity})

        for spec in CONFIG_KEYS:
            value = (resolved.get(spec.key) or "").strip()
            if self._is_required(spec, resolved) and not value:
                add(spec.key, "required_missing",
                    f"{spec.key} ist Pflicht ({spec.description})")
                continue
            if not value:
                continue
            if spec.type == "int" and not _is_int(value):
                add(spec.key, "invalid_int", f"{spec.key}: '{value}' ist keine ganze Zahl")
            elif spec.type == "float" and not _is_float(value):
                add(spec.key, "invalid_float", f"{spec.key}: '{value}' ist keine Zahl")
            elif spec.type == "bool" and value.lower() not in {"true", "false", "0", "1"}:
                add(spec.key, "invalid_bool", f"{spec.key}: '{value}' ist kein Wahrheitswert")
            elif spec.type == "choice" and value not in spec.choices:
                add(spec.key, "invalid_choice",
                    f"{spec.key}: '{value}' nicht erlaubt (erlaubt: {', '.join(spec.choices)})")
            elif spec.key == "DATABASE_URL" and not value.startswith(("postgresql://", "postgres://")):
                add(spec.key, "invalid_dsn", "DATABASE_URL muss mit postgresql:// beginnen")
        return issues

    @staticmethod
    def _is_required(spec: ConfigKey, resolved: Mapping[str, str]) -> bool:
        if spec.required_if == "*":
            return True
        if not spec.required_if:
            return False
        cond_key, _, cond_value = spec.required_if.partition("==")
        return (resolved.get(cond_key) or "").strip() == cond_value

    def startup_status(self) -> dict[str, Any]:
        """Startvalidierung: fehlende Pflichtwerte => klarer BLOCKED-Status."""
        resolved = self.resolve()
        issues = self.validate(resolved["values"])
        source_issues = [
            {"key": "", "code": "source_invalid", "message": msg, "severity": "warning"}
            for msg in resolved["issues"]
        ]
        blockers = [issue for issue in issues if issue["severity"] == "error"]
        return {
            "schema": SCHEMA,
            "status": STATUS_BLOCKED if blockers else STATUS_OK,
            "blockers": blockers,
            "warnings": [i for i in issues if i["severity"] != "error"] + source_issues,
            "origins": resolved["origins"],
            "paths": {
                "dotenv": str(self.dotenv_path),
                "workspace_config": str(self.workspace_config_path),
                "appdata_config": str(self.appdata_config_path),
            },
        }

    # -- Schreiben -----------------------------------------------------------
    def set_values(self, changes: Mapping[str, str], scope: str = "workspace") -> dict[str, Any]:
        """Persistiert Änderungen. Nicht-Secrets -> config.json (workspace|appdata),
        Secrets -> .env (nie in JSON). Maskierte Secrets werden übersprungen.
        """
        unknown = [key for key in changes if key not in KEYS_BY_NAME]
        if unknown:
            return {"ok": False, "errors": [f"unbekannter Key: {k}" for k in unknown], "written": []}

        current = self.resolve()["values"]
        plain: dict[str, str] = {}
        secret: dict[str, str] = {}
        for key, raw in changes.items():
            spec = KEYS_BY_NAME[key]
            value = (raw or "").strip()
            if spec.secret:
                if value == SECRET_MASK:
                    continue
                if value != current.get(key, ""):
                    secret[key] = value
            elif value != current.get(key, ""):
                plain[key] = value

        candidate = dict(current)
        candidate.update(plain)
        candidate.update(secret)
        errors = [i["message"] for i in self.validate(candidate) if i["severity"] == "error"
                  and i["key"] in set(plain) | set(secret)]
        if errors:
            return {"ok": False, "errors": errors, "written": []}

        written: list[str] = []
        if plain:
            target = self.workspace_config_path if scope == "workspace" else self.appdata_config_path
            write_json_config(target, plain)
            written.extend(plain)
        if secret:
            write_dotenv(self.dotenv_path, secret)
            written.extend(secret)
        for key, value in {**plain, **secret}.items():
            os.environ[key] = value
        return {"ok": True, "errors": [], "written": sorted(written)}

    # -- Anzeige --------------------------------------------------------------
    def snapshot(self) -> dict[str, Any]:
        """Maskierte, gegliederte Sicht für GUI/CLI (keine Secret-Werte)."""
        resolved = self.resolve()
        values, origins = resolved["values"], resolved["origins"]
        sections = []
        for section in SECTIONS:
            fields = []
            for spec in CONFIG_KEYS:
                if spec.section != section:
                    continue
                value = values[spec.key]
                fields.append({
                    "key": spec.key,
                    "label": spec.key,
                    "type": spec.type,
                    "value": SECRET_MASK if spec.secret and value else value,
                    "default": spec.default,
                    "choices": list(spec.choices),
                    "description": spec.description,
                    "secret": spec.secret,
                    "origin": origins[spec.key],
                    "required": bool(spec.required_if),
                })
            sections.append({"title": section, "fields": fields})
        return {"schema": SCHEMA, "sections": sections, "status": self.startup_status()}


def runtime_config_status(project_root: str | Path | None = None) -> dict[str, Any]:
    """CLI-/View-Model-Einstieg: Startvalidierung der zentralen Konfiguration."""
    return RuntimeConfig(project_root).startup_status()


def _is_int(value: str) -> bool:
    try:
        int(value)
        return True
    except ValueError:
        return False


def _is_float(value: str) -> bool:
    try:
        float(value)
        return True
    except ValueError:
        return False
