from pathlib import Path
from .utils import now_date
from .vault_scan import iter_markdown, read_note

def write_meeting_intelligence_v2(settings: dict) -> Path:
    vault = Path(settings["vault_path"])
    folder = vault / "69_MeetingIntelligence"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"{now_date()}_meeting-intelligence.md"

    rows = []
    for note in iter_markdown(vault):
        text = read_note(note)
        low = text.lower()
        if "meeting" in low or "agenda" in low or "protokoll" in low or "teilnehmer" in low:
            tasks = low.count("aufgabe") + low.count("- [ ]")
            decisions = low.count("entscheidung") + low.count("beschluss")
            risks = low.count("risiko") + low.count("blocker")
            rows.append((tasks, decisions, risks, note.stem))

    lines = ["# Meeting Intelligence v2", "", f"Datum: {now_date()}", "", "| Meeting | Aufgaben | Entscheidungen | Risiken | Empfehlung |", "|---|---:|---:|---:|---|"]
    if not rows:
        lines.append("| keine Meetings erkannt | 0 | 0 | 0 | Transkripte/Protokolle importieren |")
    for tasks, decisions, risks, stem in sorted(rows, reverse=True):
        rec = "Nachbereitung erzeugen" if tasks or decisions or risks else "Agenda/Ergebnis ergänzen"
        lines.append(f"| [[{stem}]] | {tasks} | {decisions} | {risks} | {rec} |")
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
