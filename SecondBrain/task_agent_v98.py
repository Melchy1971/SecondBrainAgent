from pathlib import Path
from collections import defaultdict
from .v98_common import VAULT, iter_notes, read, open_tasks, done_tasks, signals, now_date, ensure

def write_task_agent(vault: Path = VAULT) -> Path:
    target = ensure(vault / "106_TaskAgent") / f"{now_date()}_task-agent.md"
    rows = []
    for p in iter_notes(vault):
        text = read(p)
        ots = open_tasks(text)
        if ots:
            sig = signals(text)
            priority = len(ots) + sig["risk"] * 3 + sig["decision"]
            rows.append((priority, p.stem, ots[:5], sig))

    lines = ["# Task Agent v9.8", "", f"Datum: {now_date()}", "", "| Priorität | Quelle | Aufgaben | Grund |", "|---:|---|---|---|"]
    for prio, stem, tasks, sig in sorted(rows, reverse=True)[:80]:
        reason = "Risiko" if sig["risk"] else "Entscheidung" if sig["decision"] else "offene Aufgaben"
        lines.append(f"| {prio} | [[{stem}]] | {'<br>'.join(tasks)} | {reason} |")
    if not rows:
        lines.append("| 0 | keine offenen Aufgaben | - | - |")
    lines += ["", "## Nächste Aktionen", "", "- Aufgaben mit Risiko zuerst prüfen.", "- Doppelte Aufgaben zusammenführen.", "- Aufgaben ohne Projektbezug klassifizieren."]
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
