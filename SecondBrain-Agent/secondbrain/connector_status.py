from pathlib import Path
from .utils import now_date, now_datetime
from .config import load_simple_yaml

def write_connector_status(project_root: Path, settings: dict) -> Path:
    vault = Path(settings["vault_path"])
    target_dir = vault / "99_System" / "connector_status"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{now_date()}_connector-status.md"
    cfg = load_simple_yaml(project_root / "config" / "connectors.production.yaml").get("connectors", {})

    lines = [
        f"# Connector Status {now_datetime()}",
        "",
        "| Connector | Status | Hinweis |",
        "|---|---|---|"
    ]
    for name, value in cfg.items():
        enabled = value.get("enabled", False) if isinstance(value, dict) else bool(value)
        lines.append(f"| {name} | {'enabled' if enabled else 'disabled/prepared'} | konfigurieren bei Bedarf |")
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
