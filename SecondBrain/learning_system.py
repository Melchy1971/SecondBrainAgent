from pathlib import Path
from collections import Counter
from .utils import now_date
from .vault_scan import iter_markdown, read_note, extract_tags

def write_learning_report(settings: dict) -> Path:
    vault = Path(settings["vault_path"])
    folder = vault / settings.get("vault_folders", {}).get("learning", "16_Lernsystem")
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"{now_date()}_learning-report.md"

    tag_counts = Counter()
    for note in iter_markdown(vault):
        for tag in extract_tags(read_note(note)):
            tag_counts[tag] += 1

    lines = ["# Lernsystem Report", "", f"Datum: {now_date()}", "", "## Häufige Themen", ""]
    for tag, count in tag_counts.most_common(20):
        lines.append(f"- #{tag}: {count}")
    if not tag_counts:
        lines.append("- Keine Tags erkannt.")

    lines += ["", "## Lernempfehlungen", "", "- Zu Top-Themen je eine strukturierte Wissensnotiz erstellen.", "- Wissenslücken-Report prüfen."]
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
