from pathlib import Path
from .utils import now_date
from .vault_scan import iter_markdown, read_note

def extract_decision_lines(text: str) -> list[str]:
    out = []
    for line in text.splitlines():
        low = line.lower()
        if "entscheidung:" in low or "beschluss:" in low or "festlegung:" in low:
            out.append(line.split(":", 1)[-1].strip())
    return out

def write_decision_intelligence_v2(settings: dict) -> Path:
    vault = Path(settings["vault_path"])
    folder = vault / "68_DecisionIntelligence"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / "Decision_Intelligence_v2.md"

    rows = []
    for note in iter_markdown(vault):
        text = read_note(note)
        decisions = extract_decision_lines(text)
        for d in decisions:
            low = text.lower()
            quality = 0
            quality += 25 if "annahme" in low else 0
            quality += 25 if "alternative" in low else 0
            quality += 25 if "risiko" in low else 0
            quality += 25 if "ergebnis" in low or "lesson" in low else 0
            rows.append((quality, d, note.stem))

    lines = ["# Decision Intelligence v2", "", f"Aktualisiert: {now_date()}", "", "| Qualität | Entscheidung | Quelle | Fehlende Felder |", "|---:|---|---|---|"]
    if not rows:
        lines.append("| 0 | keine Entscheidungen erkannt | - | - |")
    for quality, decision, source in sorted(rows):
        missing = []
        if quality < 25: missing.append("Annahme")
        if quality < 50: missing.append("Alternative")
        if quality < 75: missing.append("Risiko")
        if quality < 100: missing.append("Ergebnis")
        lines.append(f"| {quality} | {decision} | [[{source}]] | {', '.join(missing)} |")
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
