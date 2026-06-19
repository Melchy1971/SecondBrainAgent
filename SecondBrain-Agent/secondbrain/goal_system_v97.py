from pathlib import Path
from collections import defaultdict
from .v97_common import VAULT, iter_notes, read, open_tasks, signals, now_date, ensure

CATEGORIES = {
    "Beruf": ["sap", "prozess", "telekom", "projekt", "management"],
    "Projekte": ["secondbrain", "jarvis", "wissensdatenbank", "code", "release"],
    "Lernen": ["lernen", "kurs", "skill", "ki", "python"],
    "Gesundheit": ["gesundheit", "diabetes", "training", "gewicht"],
    "Verein": ["ttc", "verein", "tischtennis", "turnier"],
    "Privat": ["reise", "familie", "haus", "finanzen"],
}

def write_goal_map(vault: Path = VAULT) -> Path:
    target = ensure(vault / "103_GoalSystem") / "Goal_Map_v97.md"
    scores = defaultdict(lambda: {"tasks":0, "risks":0, "decisions":0, "notes":0})

    for p in iter_notes(vault):
        text = read(p)
        low = text.lower()
        sig = signals(text)
        for cat, keys in CATEGORIES.items():
            if any(k in low for k in keys):
                scores[cat]["tasks"] += len(open_tasks(text))
                scores[cat]["risks"] += sig["risk"]
                scores[cat]["decisions"] += sig["decision"]
                scores[cat]["notes"] += 1

    lines = ["# Goal System v9.7", "", f"Aktualisiert: {now_date()}", "", "| Zielbereich | Notizen | Aufgaben | Risiken | Entscheidungen | Fokus |", "|---|---:|---:|---:|---:|---|"]
    for cat in CATEGORIES:
        s = scores[cat]
        focus = "Risiko senken" if s["risks"] else "Nächsten Schritt definieren" if s["tasks"] else "Material sammeln"
        lines.append(f"| {cat} | {s['notes']} | {s['tasks']} | {s['risks']} | {s['decisions']} | {focus} |")
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
