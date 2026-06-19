from pathlib import Path
from .v10_common import VAULT, iter_notes, read, open_tasks, done_tasks, signals, now_date, ensure

def write_personal_kpis(vault: Path = VAULT) -> Path:
    target = ensure(vault / "123_PersonalKPIs") / f"{now_date()}_personal-kpis.md"
    notes = list(iter_notes(vault))
    open_count = done_count = risk_count = decision_count = 0
    for p in notes:
        text = read(p)
        open_count += len(open_tasks(text))
        done_count += len(done_tasks(text))
        sig = signals(text)
        risk_count += sig["risk"]
        decision_count += sig["decision"]
    total_tasks = open_count + done_count
    completion = round((done_count / total_tasks) * 100, 1) if total_tasks else 0
    lines = ["# Personal KPIs v10", "", f"Datum: {now_date()}", "", "| KPI | Wert |", "|---|---:|",
             f"| Notizen | {len(notes)} |",
             f"| Offene Aufgaben | {open_count} |",
             f"| Erledigte Aufgaben | {done_count} |",
             f"| Aufgabenabschlussquote | {completion}% |",
             f"| Risiko-Signale | {risk_count} |",
             f"| Entscheidungs-Signale | {decision_count} |"]
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
