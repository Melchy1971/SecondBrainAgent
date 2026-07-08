from pathlib import Path
from .utils import now_date
from .vault_scan import iter_markdown, read_note, extract_tasks

def write_project_intelligence(settings: dict) -> Path:
    vault = Path(settings["vault_path"])
    folder = vault / "67_ProjectIntelligence"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"{now_date()}_project-intelligence.md"

    rows = []
    for note in iter_markdown(vault):
        text = read_note(note)
        low = text.lower()
        is_project = "01_Projekte" in note.parts or "type: project" in low or "projekt" in low[:1000]
        if is_project:
            tasks = extract_tasks(text)
            open_tasks = len([t for t in tasks if t.startswith("- [ ]")])
            risks = low.count("risiko") + low.count("blockiert") + low.count("blocked") + low.count("fail")
            activity = "hoch" if open_tasks or risks else "niedrig"
            recommendation = "Blocker/Risiken klären" if risks else "nächsten messbaren Schritt definieren"
            rows.append((risks, open_tasks, note.stem, activity, recommendation))

    lines = ["# Project Intelligence", "", f"Datum: {now_date()}", "", "| Risiko | Offene Tasks | Projekt | Aktivität | Empfehlung |", "|---:|---:|---|---|---|"]
    if not rows:
        lines.append("| 0 | 0 | keine Projekte erkannt | - | - |")
    for risks, tasks, stem, activity, recommendation in sorted(rows, reverse=True):
        lines.append(f"| {risks} | {tasks} | [[{stem}]] | {activity} | {recommendation} |")
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
