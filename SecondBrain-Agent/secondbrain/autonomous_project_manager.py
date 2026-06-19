from pathlib import Path
from .utils import now_date
from .vault_scan import iter_markdown, read_note, extract_tasks

def write_autonomous_project_plan(settings: dict) -> Path:
    vault = Path(settings["vault_path"])
    folder = vault / "45_AutonomousProjectManager"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"{now_date()}_autonomous-project-plan.md"

    projects = []
    for note in iter_markdown(vault):
        if "01_Projekte" in note.parts:
            text = read_note(note)
            tasks = extract_tasks(text)
            risk = "risiko" in text.lower() or "blockiert" in text.lower()
            projects.append((note.stem, len([t for t in tasks if t.startswith("- [ ]")]), risk))

    lines = ["# Autonomous Project Manager", "", f"Datum: {now_date()}", "", "| Projekt | Offene Tasks | Risiko | Empfehlung |", "|---|---:|---|---|"]
    for p, tasks, risk in projects:
        rec = "Risiko klären" if risk else "nächsten Schritt definieren"
        lines.append(f"| [[{p}]] | {tasks} | {'ja' if risk else 'nein'} | {rec} |")
    if not projects:
        lines.append("| Keine Projekte erkannt | 0 | nein | - |")
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
