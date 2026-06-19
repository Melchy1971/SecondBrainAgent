from pathlib import Path
from .utils import now_date, slugify
from .vault_scan import iter_markdown, read_note

def run_simulation(settings: dict, scenario: str) -> Path:
    vault = Path(settings["vault_path"])
    folder = vault / "29_Simulations"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"{now_date()}_simulation_{slugify(scenario)}.md"

    affected = []
    terms = [t for t in scenario.lower().split() if len(t) >= 4]
    for note in iter_markdown(vault):
        text = read_note(note).lower()
        if any(t in text for t in terms):
            affected.append(note.stem)

    lines = [
        f"# Simulation: {scenario}",
        "",
        f"Datum: {now_date()}",
        "",
        "## Betroffene Notizen",
        ""
    ]
    lines += [f"- [[{a}]]" for a in affected[:100]] or ["- Keine direkten Treffer."]
    lines += ["", "## Hypothese", "", "- Auswirkungen müssen fachlich geprüft werden.", "", "## Nächste Schritte", "", "- betroffene Projekte prüfen", "- Aufgaben und Risiken ableiten"]
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
