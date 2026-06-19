from pathlib import Path
from .utils import now_date
from .vault_scan import iter_markdown, read_note, extract_tasks

def write_plans(settings: dict) -> list[Path]:
    vault = Path(settings["vault_path"])
    folder = vault / "51_Planner"
    folder.mkdir(parents=True, exist_ok=True)
    open_tasks = []
    for note in iter_markdown(vault):
        for task in extract_tasks(read_note(note)):
            if task.startswith("- [ ]"):
                open_tasks.append((task, note.stem))

    specs = {
        "Daily_Plan.md": 8,
        "Weekly_Plan.md": 20,
        "Monthly_Plan.md": 40,
        "Quarterly_Plan.md": 80,
    }
    created = []
    for name, limit in specs.items():
        target = folder / name
        lines = [f"# {name.replace('_', ' ').replace('.md','')}", "", f"Aktualisiert: {now_date()}", "", "## Fokus", "", "## Aufgaben", ""]
        for task, src in open_tasks[:limit]:
            lines.append(f"- {task} ([[{src}]])")
        if not open_tasks:
            lines.append("- Keine offenen Aufgaben erkannt.")
        target.write_text("\n".join(lines), encoding="utf-8")
        created.append(target)
    return created
