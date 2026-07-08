from pathlib import Path
from collections import Counter
from .v9_common import iter_md, read, tasks, tags, now_date, ensure

def write_recommendations(vault: Path) -> Path:
    folder = ensure(vault / "77_RecommendationEngine")
    target = folder / f"{now_date()}_recommendations.md"

    open_tasks = []
    risks = []
    low_quality = []
    tag_counter = Counter()

    for p in iter_md(vault):
        text = read(p)
        tag_counter.update(tags(text))
        for t in tasks(text):
            if "- [ ]" in t:
                open_tasks.append((p.stem, t))
        low = text.lower()
        if "risiko" in low or "blockiert" in low or "blocked" in low:
            risks.append(p.stem)
        if not text.strip().startswith("---") or len(text.strip()) < 250:
            low_quality.append(p.stem)

    lines = ["# Recommendation Engine", "", f"Datum: {now_date()}", ""]
    lines += ["## Priorisierte Empfehlungen", ""]
    if risks:
        lines.append("1. Risiken prüfen: " + ", ".join(f"[[{r}]]" for r in risks[:10]))
    if open_tasks:
        lines.append("2. Offene Aufgaben konsolidieren: " + str(len(open_tasks)))
    if low_quality:
        lines.append("3. Schwache Notizen verbessern: " + ", ".join(f"[[{x}]]" for x in low_quality[:10]))
    lines += ["", "## Häufige Themen", ""]
    for tag, count in tag_counter.most_common(20):
        lines.append(f"- #{tag}: {count}")
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
