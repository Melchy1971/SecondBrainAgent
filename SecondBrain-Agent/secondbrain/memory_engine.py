from pathlib import Path
from collections import Counter
from .utils import now_date
from .vault_scan import iter_markdown, read_note, extract_tags

MEMORY_SIGNALS = ["priorität", "präferenz", "immer", "nie", "wichtig", "ziel", "arbeitsweise", "entscheidung"]

def build_memory_profile(settings: dict) -> Path:
    vault = Path(settings["vault_path"])
    folder = vault / "22_Memory"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / "Memory_Profile.md"

    tags = Counter()
    signals = []
    for note in iter_markdown(vault):
        text = read_note(note)
        lower = text.lower()
        for tag in extract_tags(text):
            tags[tag] += 1
        for line in text.splitlines():
            if any(s in line.lower() for s in MEMORY_SIGNALS):
                signals.append((note.stem, line.strip()))

    lines = ["# Memory Profile", "", f"Aktualisiert: {now_date()}", "", "## Häufige Themen", ""]
    for tag, count in tags.most_common(20):
        lines.append(f"- #{tag}: {count}")

    lines += ["", "## Signale", ""]
    for source, line in signals[:80]:
        lines.append(f"- [[{source}]]: {line[:200]}")

    lines += ["", "## Abgeleitete Arbeitspräferenzen", "", "- Struktur vor Inhalt.", "- Markdown als Source of Truth.", "- Automatisierung bevorzugt.", "- Lokale Kontrolle bevorzugt."]
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
