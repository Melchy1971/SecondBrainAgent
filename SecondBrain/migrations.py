from pathlib import Path
from .utils import now_date, now_datetime

def write_migration_status(settings: dict, project_root: Path) -> Path:
    vault = Path(settings["vault_path"])
    target_dir = vault / "99_System" / "migrations"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{now_date()}_migration-status.md"

    migrations = sorted((project_root / "migrations").glob("*.md"))
    lines = [
        f"# Migration Status {now_datetime()}",
        "",
        f"Migrationen gefunden: {len(migrations)}",
        "",
    ]
    if not migrations:
        lines.append("- Keine Migrationen vorhanden.")
    else:
        for m in migrations:
            lines.append(f"- `{m.name}`")

    target.write_text("\n".join(lines), encoding="utf-8")
    return target
