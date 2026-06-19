from pathlib import Path
import shutil
from .utils import now_date, now_datetime, ensure_unique_path

def run_backup_restore_test(project_root: Path) -> dict:
    test_root = project_root / "backups" / "restore_test"
    test_root.mkdir(parents=True, exist_ok=True)

    source = project_root / "config" / "settings.yaml"
    backup = ensure_unique_path(test_root / "settings.backup.yaml")
    restored = ensure_unique_path(test_root / "settings.restored.yaml")

    if not source.exists():
        return {"ok": False, "message": "settings.yaml fehlt"}

    shutil.copy2(source, backup)
    shutil.copy2(backup, restored)

    ok = restored.exists() and restored.read_text(encoding="utf-8") == source.read_text(encoding="utf-8")
    return {
        "ok": ok,
        "message": "Backup/Restore Test OK" if ok else "Restore-Inhalt weicht ab",
        "backup": str(backup),
        "restored": str(restored),
    }

def write_backup_restore_test_report(project_root: Path, settings: dict) -> Path:
    vault = Path(settings["vault_path"])
    target_dir = vault / "99_System" / "backup_restore_tests"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{now_date()}_backup-restore-test.md"
    result = run_backup_restore_test(project_root)

    lines = [
        f"# Backup Restore Test {now_datetime()}",
        "",
        f"Status: **{'PASS' if result['ok'] else 'FAIL'}**",
        "",
        f"Message: {result['message']}",
        "",
        f"Backup: `{result.get('backup', '-')}`",
        f"Restored: `{result.get('restored', '-')}`",
    ]
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
