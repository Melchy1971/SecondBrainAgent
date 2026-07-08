from pathlib import Path
from .utils import now_date, now_datetime

def append_journal(settings: dict, imported_items: list[dict]) -> Path | None:
    if not settings.get("journal_enabled", True):
        return None

    vault = Path(settings["vault_path"])
    journal_folder = settings.get("vault_folders", {}).get("journal", "06_Journal")
    target_dir = vault / journal_folder
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{now_date()}.md"

    if not target.exists():
        target.write_text(f"# Journal {now_date()}\n\n## Neue Inhalte\n\n## Aufgaben\n\n## Entscheidungen\n\n## Notizen\n\n", encoding="utf-8")

    with target.open("a", encoding="utf-8") as f:
        f.write(f"\n## Importlauf {now_datetime()}\n\n")
        if not imported_items:
            f.write("- Keine neuen Inhalte.\n")
        for item in imported_items:
            f.write(f"- [[{Path(item['target']).stem}]] aus `{item['provider']}` → `{item['type']}`\n")

    return target
