from pathlib import Path
import shutil
from .utils import now_date, ensure_unique_path

def archive_source(project_root: Path, source: Path, status: str = "processed") -> Path:
    target_dir = project_root / "archive" / status / now_date() / source.parent.name
    target_dir.mkdir(parents=True, exist_ok=True)
    target = ensure_unique_path(target_dir / source.name)
    shutil.move(str(source), str(target))
    return target
