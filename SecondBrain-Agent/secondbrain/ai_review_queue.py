from pathlib import Path
from .utils import now_date, ensure_unique_path
from .ai_layer_real import ai_review_note
from .vault_scan import read_note

def review_one_file(project_root: Path, settings: dict, file_path: str) -> Path:
    source = Path(file_path)
    text = read_note(source)
    reviewed = ai_review_note(project_root, text)
    vault = Path(settings["vault_path"])
    target_dir = vault / "99_System" / "ai_reviews"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = ensure_unique_path(target_dir / f"{now_date()}_{source.stem}_reviewed.md")
    target.write_text(reviewed, encoding="utf-8")
    return target
