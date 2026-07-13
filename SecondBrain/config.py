from pathlib import Path
import json

from .path import from_settings_service

def parse_value(value: str):
    value = value.strip()
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    if value.isdigit():
        return int(value)
    return value

def load_simple_yaml(path: Path) -> dict:
    data = {}
    if not path.exists():
        return data

    current_parent = None
    current_child = None

    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.strip().startswith("#"):
            continue

        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()

        if indent == 0 and line.endswith(":"):
            current_parent = line[:-1]
            data[current_parent] = {}
            current_child = None
            continue

        if indent == 2 and current_parent and line.endswith(":"):
            current_child = line[:-1]
            data[current_parent][current_child] = {}
            continue

        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = parse_value(value)

            if indent == 0:
                data[key] = value
                current_parent = None
                current_child = None
            elif indent == 2 and current_parent:
                data[current_parent][key] = value
            elif indent == 4 and current_parent and current_child:
                data[current_parent][current_child][key] = value

    return data

def load_settings(project_root: Path) -> dict:
    settings = load_simple_yaml(project_root / "config" / "settings.yaml")
    vault = load_simple_yaml(project_root / "config" / "vault.yaml")
    providers = load_simple_yaml(project_root / "config" / "providers.yaml")
    settings["project_root"] = str(project_root)
    settings.setdefault("vault_path", str(project_root / "SecondBrain"))
    settings.setdefault("incoming_path", str(project_root / "SecondBrain-Inbox"))

    desktop_settings_path = project_root / "data" / "desktop_app" / "settings.json"
    try:
        desktop_settings = json.loads(desktop_settings_path.read_text(encoding="utf-8")) if desktop_settings_path.exists() else {}
    except Exception:
        desktop_settings = {}

    class _DesktopSettingsAdapter:
        def __init__(self, values: dict) -> None:
            self._values = values if isinstance(values, dict) else {}

        def get(self, key: str) -> object:
            if key in self._values:
                return self._values[key]
            if key == "paths.vault":
                return self._values.get("vault_path", self._values.get("vault", ""))
            if key == "paths.incoming":
                return self._values.get("incoming_path", self._values.get("inbox_path", self._values.get("incoming", "")))
            return ""

    app_paths = from_settings_service(_DesktopSettingsAdapter(desktop_settings), project_root)
    settings["vault_path"] = str(app_paths.vault)
    settings["incoming_path"] = str(app_paths.incoming)
    settings["paths.vault"] = str(app_paths.vault)
    settings["paths.incoming"] = str(app_paths.incoming)
    settings["vault_folders"] = vault.get("folders", {})
    settings["providers"] = providers.get("providers", {})
    return settings
