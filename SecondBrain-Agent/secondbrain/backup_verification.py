from pathlib import Path
from .utils import now_date, now_datetime

def verify_backups(project_root: Path, settings: dict) -> Path:
    vault = Path(settings["vault_path"])
    target_dir = vault / "99_System" / "backup_verification"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{now_date()}_backup-verification.md"

    backup_root = project_root / "backups"
    backups = sorted([p for p in backup_root.iterdir() if p.is_dir()], reverse=True) if backup_root.exists() else []
    latest = backups[0] if backups else None

    checks = []
    checks.append(("backup_root_exists", backup_root.exists()))
    checks.append(("at_least_one_backup", bool(backups)))
    if latest:
        checks.append(("latest_has_config", (latest / "config").exists()))
        checks.append(("latest_has_cache", (latest / "cache").exists()))

    lines = [
        f"# Backup Verification {now_datetime()}",
        "",
        f"Backups gefunden: {len(backups)}",
        f"Letztes Backup: `{latest}`" if latest else "Letztes Backup: keines",
        "",
        "| Check | Status |",
        "|---|---|",
    ]
    for name, ok in checks:
        lines.append(f"| {name} | {'PASS' if ok else 'FAIL'} |")
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
