from pathlib import Path
from collections import defaultdict
from .v10_common import VAULT, iter_notes, read, open_tasks, done_tasks, domain_of, signals, now_date, ensure

def write_weekly_os(vault: Path = VAULT) -> Path:
    target = ensure(vault / "122_WeeklyOperatingSystem") / f"{now_date()}_weekly-os.md"
    stats = defaultdict(lambda: {"notes":0, "open":0, "done":0, "risks":0, "decisions":0})
    for p in iter_notes(vault):
        text = read(p)
        d = domain_of(p, text)
        sig = signals(text)
        stats[d]["notes"] += 1
        stats[d]["open"] += len(open_tasks(text))
        stats[d]["done"] += len(done_tasks(text))
        stats[d]["risks"] += sig["risk"]
        stats[d]["decisions"] += sig["decision"]
    lines = ["# Weekly Operating System v10", "", f"Datum: {now_date()}", "", "| Bereich | Notizen | Offen | Erledigt | Risiken | Entscheidungen | Wochenfokus |", "|---|---:|---:|---:|---:|---:|---|"]
    for d, s in sorted(stats.items()):
        focus = "Risiken senken" if s["risks"] else "Offene Aufgaben reduzieren" if s["open"] else "Fortschritt dokumentieren"
        lines.append(f"| {d} | {s['notes']} | {s['open']} | {s['done']} | {s['risks']} | {s['decisions']} | {focus} |")
    lines += ["", "## Review-Fragen", "", "- Was wurde erreicht?", "- Was wurde gelernt?", "- Was wird nächste Woche priorisiert?"]
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
