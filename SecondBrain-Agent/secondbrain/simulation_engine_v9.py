from pathlib import Path
from .v9_common import iter_md, read, now_date, slug, ensure

def simulate(vault: Path, scenario: str) -> Path:
    folder = ensure(vault / "79_SimulationEngineV2")
    target = folder / f"{now_date()}_simulation_{slug(scenario)}.md"
    terms = [x.lower() for x in scenario.split() if len(x) > 3]
    hits = []
    for p in iter_md(vault):
        text = read(p).lower()
        score = sum(text.count(t) for t in terms)
        if score:
            hits.append((score, p.stem))
    lines = [f"# Simulation: {scenario}", "", f"Datum: {now_date()}", "", "| Relevanz | Betroffene Notiz |", "|---:|---|"]
    for score, stem in sorted(hits, reverse=True)[:50]:
        lines.append(f"| {score} | [[{stem}]] |")
    if not hits:
        lines.append("| 0 | keine Treffer |")
    lines += ["", "## Analyse", "", "- Auswirkungen fachlich prüfen.", "- Risiken, Tasks und Entscheidungen ableiten."]
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
