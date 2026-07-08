from pathlib import Path
from collections import Counter
from .utils import now_date
from .vault_scan import iter_markdown, read_note, extract_tags

def write_digital_twin_v5(settings: dict) -> Path:
    vault = Path(settings["vault_path"])
    folder = vault / "73_DigitalTwin"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / "Digital_Twin_v5.md"

    tags = Counter()
    signals = Counter()
    for note in iter_markdown(vault):
        text = read_note(note).lower()
        tags.update(extract_tags(read_note(note)))
        for sig in ["automatisierung", "stabilität", "wartbarkeit", "lokal", "prozess", "projekt", "risiko", "entscheidung", "tischtennis", "gesundheit"]:
            if sig in text:
                signals[sig] += text.count(sig)

    lines = ["# Digital Twin v5", "", f"Aktualisiert: {now_date()}", "", "## Prioritätsmodell", ""]
    for sig, count in signals.most_common(20):
        lines.append(f"- {sig}: {count}")
    lines += ["", "## Wissensprofil", ""]
    for tag, count in tags.most_common(20):
        lines.append(f"- #{tag}: {count}")
    lines += ["", "## Simulationen", "", "- Wie würde Markus priorisieren?", "- Welche Risiken sind relevant?", "- Welche Struktur ist wartbar?"]
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
