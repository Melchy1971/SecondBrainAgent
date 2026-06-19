from pathlib import Path
from .utils import now_date, slugify, ensure_unique_path

def write_task_files(settings: dict, source_note: Path, tasks: list[str], provider: str) -> list[Path]:
    if not settings.get("create_task_files", True):
        return []

    if not tasks:
        return []

    vault = Path(settings["vault_path"])
    folder = settings.get("vault_folders", {}).get("tasks", "04_Tasks")
    target_dir = vault / folder
    target_dir.mkdir(parents=True, exist_ok=True)

    created = []
    for task in tasks:
        title = task[:90]
        filename = f"{now_date()}_{slugify(title)}.md"
        target = ensure_unique_path(target_dir / filename)

        md = (
            "---\n"
            f"title: \"{title}\"\n"
            "type: task\n"
            "status: open\n"
            f"created: {now_date()}\n"
            f"provider: \"{provider}\"\n"
            f"source_note: \"[[{source_note.stem}]]\"\n"
            "tags:\n"
            "  - task\n"
            "---\n\n"
            "# Aufgabe\n\n"
            f"- [ ] {task}\n\n"
            "# Quelle\n\n"
            f"[[{source_note.stem}]]\n"
        )

        target.write_text(md, encoding="utf-8")
        created.append(target)

    return created
