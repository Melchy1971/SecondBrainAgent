from pathlib import Path
from .v98_common import VAULT, iter_notes, read, signals, now_date, ensure

def write_decision_agent(vault: Path = VAULT) -> Path:
    target = ensure(vault / "110_DecisionAgent") / f"{now_date()}_decision-agent.md"
    rows = []
    for p in iter_notes(vault):
        text = read(p)
        sig = signals(text)
        low = text.lower()
        if sig["decision"] or "entscheidung" in low:
            quality = 0
            quality += 25 if "annahme" in low else 0
            quality += 25 if "alternative" in low else 0
            quality += 25 if "risiko" in low else 0
            quality += 25 if "ergebnis" in low or "wirkung" in low else 0
            missing = []
            if "annahme" not in low: missing.append("Annahmen")
            if "alternative" not in low: missing.append("Alternativen")
            if "risiko" not in low: missing.append("Risiken")
            if "ergebnis" not in low and "wirkung" not in low: missing.append("Ergebnis/Wirkung")
            rows.append((100-quality, p.stem, quality, missing))
    lines = ["# Decision Agent v9.8", "", f"Datum: {now_date()}", "", "| Reviewbedarf | Entscheidung | Qualität | Fehlende Felder |", "|---:|---|---:|---|"]
    for need, stem, quality, missing in sorted(rows, reverse=True)[:80]:
        lines.append(f"| {need} | [[{stem}]] | {quality} | {', '.join(missing) if missing else 'vollständig'} |")
    if not rows:
        lines.append("| 0 | keine Entscheidungen erkannt | 0 | - |")
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
