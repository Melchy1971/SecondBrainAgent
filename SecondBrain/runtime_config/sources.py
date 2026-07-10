"""Leser/Schreiber der einzelnen Konfigurationsquellen.

JSON-Quellen dürfen für Secret-Keys nur Referenzen ({"ref": "ENV_NAME"}) enthalten.
Rohwerte für Secret-Keys in JSON werden gemeldet und ignoriert.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from secondbrain.runtime_config.schema import KEYS_BY_NAME

SOURCE_ENV = "environ"
SOURCE_DOTENV = "dotenv"
SOURCE_WORKSPACE = "workspace_config"
SOURCE_APPDATA = "appdata_config"
SOURCE_GUI_LEGACY = "gui_settings_legacy"
SOURCE_DEFAULT = "default"

PRECEDENCE: tuple[str, ...] = (
    SOURCE_ENV, SOURCE_DOTENV, SOURCE_WORKSPACE, SOURCE_APPDATA, SOURCE_GUI_LEGACY, SOURCE_DEFAULT,
)


def read_dotenv(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        values[key.strip()] = value.strip()
    return values


def write_dotenv(path: Path, changes: Mapping[str, str]) -> list[str]:
    """Aktualisiert nur die übergebenen Keys; Kommentare/fremde Zeilen bleiben erhalten."""
    if not changes:
        return []
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    remaining = dict(changes)
    out: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key = stripped.partition("=")[0].strip()
            if key in remaining:
                out.append(f"{key}={remaining.pop(key)}")
                continue
        out.append(line)
    if remaining:
        if out and out[-1].strip():
            out.append("")
        out.append("# --- ergänzt durch RuntimeConfig ---")
        out.extend(f"{key}={value}" for key, value in remaining.items())
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return sorted(changes)


def read_json_config(path: Path) -> tuple[dict[str, str], list[str]]:
    """Liest eine JSON-Quelle. Returns (werte, issues).

    Secret-Keys: nur {"ref": "ENV_NAME"} zulässig; der Wert selbst wird NIE aus
    JSON gelesen. Die Referenz bestimmt, unter welchem env-/dotenv-Namen der
    Wert aufgelöst wird (Standard: Key-Name selbst).
    """
    if not path.exists():
        return {}, []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {}, [f"{path.name}: nicht lesbar ({type(exc).__name__})"]
    if not isinstance(data, dict):
        return {}, [f"{path.name}: erwartet JSON-Objekt"]
    values: dict[str, str] = {}
    issues: list[str] = []
    for key, raw in data.items():
        spec = KEYS_BY_NAME.get(key)
        if spec is None:
            continue  # fremde Keys tolerieren (z.B. Alt-GUI-Settings)
        if spec.secret:
            if isinstance(raw, dict) and set(raw.keys()) == {"ref"}:
                values[f"{key}::ref"] = str(raw["ref"])
            else:
                issues.append(
                    f"{path.name}: Secret '{key}' darf nur als Referenz "
                    '({"ref": "ENV_NAME"}) gespeichert werden — Wert ignoriert'
                )
            continue
        values[key] = _as_str(raw)
    return values, issues


def write_json_config(path: Path, changes: Mapping[str, Any]) -> None:
    """Merged Nicht-Secret-Änderungen in eine JSON-Quelle (Secrets werden abgewiesen)."""
    for key in changes:
        spec = KEYS_BY_NAME.get(key)
        if spec is not None and spec.secret:
            raise ValueError(f"Secret '{key}' darf nicht in {path.name} geschrieben werden")
    existing: dict[str, Any] = {}
    if path.exists():
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                existing = loaded
        except (OSError, json.JSONDecodeError):
            existing = {}
    existing.update({key: _as_str(value) for key, value in changes.items()})
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(existing, indent=2, sort_keys=True, ensure_ascii=False), encoding="utf-8")


def _as_str(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return "" if value is None else str(value)
