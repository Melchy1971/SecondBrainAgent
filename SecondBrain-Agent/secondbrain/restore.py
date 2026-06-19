from pathlib import Path
import shutil

def list_backups(project_root: Path) -> list[Path]:
    backup_root = project_root / "backups"
    if not backup_root.exists():
        return []
    return sorted([p for p in backup_root.iterdir() if p.is_dir()], reverse=True)

def restore_latest_config_cache(project_root: Path) -> Path | None:
    backups = list_backups(project_root)
    if not backups:
        return None
    latest = backups[0]
    for rel in ["config", "cache"]:
        src = latest / rel
        dst = project_root / rel
        if src.exists():
            shutil.copytree(src, dst, dirs_exist_ok=True)
    return latest
