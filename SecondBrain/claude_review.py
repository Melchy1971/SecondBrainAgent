from pathlib import Path
from .utils import now_date, now_datetime

def write_review_item(settings: dict, source_note: Path, note_type: str, reason: str) -> Path | None:
    if not settings.get("create_claude_review_queue", True):
        return None

    vault = Path(settings["vault_path"])
    system_folder = settings.get("vault_folders", {}).get("system", "99_System")
    target_dir = vault / system_folder / "claude_review"
    target_dir.mkdir(parents=True, exist_ok=True)

    target = target_dir / f"{now_date()}_review-queue.md"

    if not target.exists():
        target.write_text(f"# Claude Review Queue {now_date()}\n\n", encoding="utf-8")

    with target.open("a", encoding="utf-8") as f:
        f.write(f"## {now_datetime()}\n\n")
        f.write(f"- Datei: [[{source_note.stem}]]\n")
        f.write(f"- Typ: `{note_type}`\n")
        f.write(f"- Grund: {reason}\n")
        f.write("- Aktion: Inhalt prüfen, Titel verbessern, Backlinks ergänzen, Tags bereinigen.\n\n")

    return target
