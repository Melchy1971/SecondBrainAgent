from pathlib import Path

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
    settings["vault_folders"] = vault.get("folders", {})
    settings["providers"] = providers.get("providers", {})
    return settings
