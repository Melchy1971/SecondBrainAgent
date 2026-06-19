from pathlib import Path
from collections import defaultdict
from .v10_common import VAULT, iter_notes, read, open_tasks, done_tasks, domain_of, signals, now_date, ensure

def write_life_dashboard(vault: Path = VAULT) -> Path:
    target = ensure(vault / "120_LifeDashboard") / "Life_Dashboard_v10.md"
    stats = defaultdict(lambda: {"notes":0, "open_tasks":0, "done_tasks":0, "risks":0, "decisions":0})

    for p in iter_notes(vault):
        text = read(p)
        d = domain_of(p, text)
        sig = signals(text)
        stats[d]["notes"] += 1
        stats[d]["open_tasks"] += len(open_tasks(text))
        stats[d]["done_tasks"] += len(done_tasks(text))
        stats[d]["risks"] += sig["risk"]
        stats[d]["decisions"] += sig["decision"]

    lines = ["# Life Dashboard v10", "", f"Aktualisiert: {now_date()}", "", "| Bereich | Notizen | Offen | Erledigt | Risiken | Entscheidungen | Fokus |", "|---|---:|---:|---:|---:|---:|---|"]
    for domain, s in sorted(stats.items()):
        focus = "Risiko prüfen" if s["risks"] else "Aufgaben priorisieren" if s["open_tasks"] else "nächsten Schritt definieren"
        lines.append(f"| {domain} | {s['notes']} | {s['open_tasks']} | {s['done_tasks']} | {s['risks']} | {s['decisions']} | {focus} |")
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
