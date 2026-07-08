from pathlib import Path

def load_secrets(project_root: Path) -> dict:
    path = project_root / "config" / "secrets.local.yaml"
    if not path.exists():
        return {}
    data = {}
    current = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.strip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()
        if indent == 0 and line.endswith(":"):
            current = line[:-1]
            data[current] = {}
        elif ":" in line and current:
            k, v = line.split(":", 1)
            data[current][k.strip()] = v.strip().strip('"')
    return data

def get_secret(project_root: Path, group: str, key: str, default: str = "") -> str:
    return load_secrets(project_root).get(group, {}).get(key, default)
