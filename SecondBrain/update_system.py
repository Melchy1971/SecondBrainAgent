from pathlib import Path
from .utils import now_date, now_datetime

def write_update_status(settings: dict) -> Path:
    vault = Path(settings["vault_path"])
    target_dir = vault / "99_System" / "update_status"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{now_date()}_update-status.md"
    lines = [
        f"# Update Status {now_datetime()}",
        "",
        "## Version",
        "",
        "- installiert: v7.0.0",
        "- Update-Modus: manuell",
        "",
        "## Regeln",
        "",
        "- Vor Update Backup erstellen.",
        "- Production Gate nach Update ausführen.",
        "- Keine automatische Überschreibung von `secrets.local.yaml`.",
    ]
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
