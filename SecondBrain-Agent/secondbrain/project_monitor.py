from pathlib import Path
from .utils import now_date
from .vault_scan import iter_markdown, read_note, note_type, extract_tasks

def write_project_monitor(settings: dict) -> Path:
    vault = Path(settings["vault_path"])
    target_dir = vault / settings.get("vault_folders", {}).get("system", "99_System") / "process_intelligence"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{now_date()}_project-monitor.md"

    projects = []
    for note in iter_markdown(vault):
        text = read_note(note)
        if note_type(text) == "project" or "01_Projekte" in note.parts:
            tasks = extract_tasks(text)
            open_tasks = [t for t in tasks if t.startswith("- [ ]")]
            blocked = "blocked" in text.lower() or "blockiert" in text.lower()
            risk = "risiko" in text.lower() or "risk" in text.lower()
            projects.append((note, len(open_tasks), blocked, risk))

    lines = ["# Projektmonitor", "", f"Datum: {now_date()}", "", "| Projekt | Offene Aufgaben | Blockiert | Risiko |", "|---|---:|---|---|"]
    if not projects:
        lines.append("| Keine Projekte erkannt | 0 | nein | nein |")
    for note, count, blocked, risk in sorted(projects, key=lambda x: x[0].stem.lower()):
        lines.append(f"| [[{note.stem}]] | {count} | {'ja' if blocked else 'nein'} | {'ja' if risk else 'nein'} |")
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
