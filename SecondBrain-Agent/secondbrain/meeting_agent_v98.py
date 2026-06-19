from pathlib import Path
from .v98_common import VAULT, iter_notes, read, open_tasks, signals, now_date, ensure

def write_meeting_agent(vault: Path = VAULT) -> Path:
    target = ensure(vault / "108_MeetingAgent") / f"{now_date()}_meeting-agent.md"
    rows = []
    for p in iter_notes(vault):
        text = read(p)
        sig = signals(text)
        if sig["meeting"]:
            rows.append((sig["meeting"] + sig["risk"]*2 + sig["decision"]*2, p.stem, len(open_tasks(text)), sig))
    lines = ["# Meeting Agent v9.8", "", f"Datum: {now_date()}", "", "| Score | Meeting | Aufgaben | Entscheidungen | Risiken | Empfehlung |", "|---:|---|---:|---:|---:|---|"]
    for score, stem, task_count, sig in sorted(rows, reverse=True)[:60]:
        rec = "Protokoll prüfen" if task_count or sig["decision"] else "Ergebnis ergänzen"
        lines.append(f"| {score} | [[{stem}]] | {task_count} | {sig['decision']} | {sig['risk']} | {rec} |")
    if not rows:
        lines.append("| 0 | keine Meetings erkannt | 0 | 0 | 0 | Transkripte importieren |")
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
