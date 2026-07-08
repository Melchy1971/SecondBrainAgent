from pathlib import Path
import shutil

def reset_cache(project_root: Path) -> list[str]:
    changed = []
    cache = project_root / "cache" / "processed_files.json"
    if cache.exists():
        cache.unlink()
        changed.append(str(cache))
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text("{}", encoding="utf-8")
    changed.append("processed_files.json neu erstellt")
    return changed

def reset_logs(project_root: Path) -> list[str]:
    changed = []
    logs = project_root / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    for p in logs.glob("*.log"):
        p.unlink()
        changed.append(str(p))
    return changed
