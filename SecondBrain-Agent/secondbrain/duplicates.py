import json
from pathlib import Path
from .utils import file_hash

def cache_file(root: Path) -> Path:
    p = root / "cache" / "processed_files.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        p.write_text("{}", encoding="utf-8")
    return p

def load(root: Path) -> dict:
    return json.loads(cache_file(root).read_text(encoding="utf-8"))

def save(root: Path, data: dict):
    cache_file(root).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def is_processed(root: Path, file: Path) -> bool:
    return file_hash(file) in load(root)

def mark_processed(root: Path, source: Path, target: Path):
    data = load(root)
    data[file_hash(source)] = {"source": str(source), "target": str(target)}
    save(root, data)
