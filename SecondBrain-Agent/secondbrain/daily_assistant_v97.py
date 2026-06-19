from pathlib import Path
from .v97_common import VAULT, iter_notes, read, open_tasks, signals, now_date, ensure

def write_daily_assistant(vault: Path = VAULT) -> Path:
    target = ensure(vault / "104_DailyAssistant") / f"{now_date()}_daily-assistant.md"
    risky = []
    todo = []
    decisions = []
    for p in iter_notes(vault):
        text = read(p)
        sig = signals(text)
        if sig["risk"]:
            risky.append((sig["risk"], p.stem))
        ots = open_tasks(text)
        if ots:
            todo.append((len(ots), p.stem, ots[:3]))
        if sig["decision"]:
            decisions.append((sig["decision"], p.stem))

    lines = ["# Daily Assistant v9.7", "", f"Datum: {now_date()}", "", "## Heute wichtig", ""]
    for score, stem in sorted(risky, reverse=True)[:5]:
        lines.append(f"- Risiko prüfen: [[{stem}]] ({score})")
    for count, stem, items in sorted(todo, reverse=True)[:5]:
        lines.append(f"- Aufgaben prüfen: [[{stem}]] ({count})")
    if not risky and not todo:
        lines.append("- Keine kritischen Signale.")
    lines += ["", "## Offene Entscheidungen", ""]
    for score, stem in sorted(decisions, reverse=True)[:10]:
        lines.append(f"- [[{stem}]]")
    if not decisions:
        lines.append("- Keine.")
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
