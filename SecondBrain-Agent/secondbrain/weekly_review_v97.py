from pathlib import Path
from .v97_common import VAULT, iter_notes, read, open_tasks, signals, now_date, ensure

def write_weekly_review(vault: Path = VAULT) -> Path:
    target = ensure(vault / "105_WeeklyReview") / f"{now_date()}_weekly-review.md"
    notes = list(iter_notes(vault))
    task_count = 0
    risk_count = 0
    decision_count = 0
    for p in notes:
        text = read(p)
        task_count += len(open_tasks(text))
        sig = signals(text)
        risk_count += sig["risk"]
        decision_count += sig["decision"]

    lines = [
        "# Weekly Review v9.7",
        "",
        f"Datum: {now_date()}",
        "",
        "## Kennzahlen",
        "",
        f"- Notizen gesamt: {len(notes)}",
        f"- Offene Aufgaben: {task_count}",
        f"- Risiko-Signale: {risk_count}",
        f"- Entscheidungs-Signale: {decision_count}",
        "",
        "## Review-Fragen",
        "",
        "- Was wurde erreicht?",
        "- Was wurde gelernt?",
        "- Was ist blockiert?",
        "- Welche Entscheidung fehlt?",
        "- Was ist der wichtigste nächste Schritt?",
    ]
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
