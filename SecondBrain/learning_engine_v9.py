from pathlib import Path
from collections import Counter
from .v9_common import iter_md, read, tags, now_date, ensure

def write_learning_plan(vault: Path) -> Path:
    folder = ensure(vault / "78_LearningEngine")
    target = folder / f"{now_date()}_learning-plan.md"
    tag_counter = Counter()
    for p in iter_md(vault):
        tag_counter.update(tags(read(p)))

    lines = ["# Learning Engine", "", f"Datum: {now_date()}", "", "## Lernfelder aus deinem Vault", ""]
    for tag, count in tag_counter.most_common(15):
        lines.append(f"### {tag}")
        lines.append(f"- vorhandene Notizen: {count}")
        lines.append("- nächster Schritt: 3 Kernnotizen lesen, 5 Karteikarten erstellen, 1 Praxisaufgabe definieren")
        lines.append("")
    if not tag_counter:
        lines.append("- Noch keine Tags erkannt.")
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
