from pathlib import Path
from .v98_common import VAULT, iter_notes, read, open_tasks, signals, now_date, ensure

def write_project_agent(vault: Path = VAULT) -> Path:
    target = ensure(vault / "109_ProjectAgent") / f"{now_date()}_project-agent.md"
    rows = []
    for p in iter_notes(vault):
        text = read(p)
        sig = signals(text)
        is_project = "01_Projekte" in p.parts or sig["project"] > 0 or "type: project" in text.lower()
        if is_project:
            tasks = len(open_tasks(text))
            score = tasks * 2 + sig["risk"] * 4 + sig["decision"] * 2
            status = "kritisch" if sig["risk"] else "aktiv" if tasks else "unklar"
            rows.append((score, p.stem, tasks, sig, status))
    lines = ["# Project Agent v9.8", "", f"Datum: {now_date()}", "", "| Score | Projekt | Aufgaben | Risiken | Entscheidungen | Status | Nächster Schritt |", "|---:|---|---:|---:|---:|---|---|"]
    for score, stem, tasks, sig, status in sorted(rows, reverse=True)[:80]:
        next_step = "Risiko klären" if sig["risk"] else "Aufgaben priorisieren" if tasks else "Projektziel ergänzen"
        lines.append(f"| {score} | [[{stem}]] | {tasks} | {sig['risk']} | {sig['decision']} | {status} | {next_step} |")
    if not rows:
        lines.append("| 0 | keine Projekte | 0 | 0 | 0 | - | /plan nutzen |")
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
