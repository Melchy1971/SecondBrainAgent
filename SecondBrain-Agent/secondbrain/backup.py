from pathlib import Path
import shutil
from .utils import now_date, now_datetime, slugify

def create_backup(project_root: Path) -> Path:
    stamp = now_datetime().replace(":", "-").replace(" ", "_")
    target = project_root / "backups" / f"backup_{stamp}"
    target.mkdir(parents=True, exist_ok=True)

    for rel in ["config", "cache", "logs"]:
        src = project_root / rel
        if src.exists():
            dst = target / rel
            if src.is_dir():
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)

    marker = target / "BACKUP_INFO.md"
    marker.write_text(
        f"# Backup\n\nDatum: {now_datetime()}\n\nQuelle: `{project_root}`\n",
        encoding="utf-8"
    )
    return target
