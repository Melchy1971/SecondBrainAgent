from pathlib import Path
from .v10_common import VAULT, iter_notes, read, open_tasks, domain_of, signals, now_date, ensure

def write_daily_os(vault: Path = VAULT) -> Path:
    target = ensure(vault / "121_DailyOperatingSystem") / f"{now_date()}_daily-os.md"
    risks, tasks, decisions = [], [], []
    for p in iter_notes(vault):
        text = read(p)
        sig = signals(text)
        domain = domain_of(p, text)
        if sig["risk"]:
            risks.append((sig["risk"], domain, p.stem))
        ots = open_tasks(text)
        if ots:
            tasks.append((len(ots), domain, p.stem, ots[:3]))
        if sig["decision"]:
            decisions.append((sig["decision"], domain, p.stem))

    lines = ["# Daily Operating System v10", "", f"Datum: {now_date()}", "", "## Heute wichtig", ""]
    for score, domain, stem in sorted(risks, reverse=True)[:5]:
        lines.append(f"- Risiko: [[{stem}]] ({domain}, Score {score})")
    for count, domain, stem, items in sorted(tasks, reverse=True)[:5]:
        lines.append(f"- Aufgaben: [[{stem}]] ({domain}, {count})")
    if not risks and not tasks:
        lines.append("- Keine kritischen Signale.")
    lines += ["", "## Entscheidungen", ""]
    for score, domain, stem in sorted(decisions, reverse=True)[:8]:
        lines.append(f"- [[{stem}]] ({domain})")
    if not decisions:
        lines.append("- Keine offenen Entscheidungssignale.")
    lines += ["", "## Tagesfragen", "", "- Was ist heute die wichtigste Sache?", "- Was darf heute nicht liegen bleiben?", "- Welche Entscheidung blockiert Fortschritt?"]
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
