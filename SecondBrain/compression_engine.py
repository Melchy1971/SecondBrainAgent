from pathlib import Path
from collections import Counter
from .utils import now_date
from .vault_scan import iter_markdown, read_note, extract_tags

def compress_knowledge(settings: dict) -> Path:
    vault = Path(settings["vault_path"])
    folder = vault / "25_Compression"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"{now_date()}_knowledge-compression.md"

    tag_counts = Counter()
    samples = {}
    for note in iter_markdown(vault):
        text = read_note(note)
        for tag in extract_tags(text):
            tag_counts[tag] += 1
            samples.setdefault(tag, []).append(note.stem)

    lines = ["# Knowledge Compression", "", f"Datum: {now_date()}", "", "## Kernideen", ""]
    for tag, count in tag_counts.most_common(20):
        lines.append(f"### {tag}")
        lines.append(f"- Vorkommen: {count}")
        lines.append("- Quellen: " + ", ".join(f"[[{s}]]" for s in samples.get(tag, [])[:8]))
        lines.append("- Executive Summary: manuell/LLM nachverdichten.")
        lines.append("")
    if not tag_counts:
        lines.append("- Keine Tags für Kompression erkannt.")
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
