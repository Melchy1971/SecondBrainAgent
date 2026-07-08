from pathlib import Path
from collections import defaultdict, Counter
from .utils import now_date
from .vault_scan import iter_markdown, read_note, extract_links, extract_tags, note_type

def build_context_map(settings: dict) -> Path:
    vault = Path(settings["vault_path"])
    folder = vault / "21_Context"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"{now_date()}_context-map.md"

    contexts = defaultdict(lambda: {"notes": [], "tags": Counter(), "types": Counter(), "links": Counter()})

    for note in iter_markdown(vault):
        text = read_note(note)
        tags = extract_tags(text)
        ntype = note_type(text) or "unknown"
        links = extract_links(text)
        key = tags[0] if tags else ntype
        contexts[key]["notes"].append(note.stem)
        contexts[key]["types"][ntype] += 1
        for tag in tags:
            contexts[key]["tags"][tag] += 1
        for link in links:
            contexts[key]["links"][link] += 1

    lines = ["# Context Map", "", f"Datum: {now_date()}", ""]
    for ctx, data in sorted(contexts.items()):
        lines += [f"## {ctx}", "", f"- Notizen: {len(data['notes'])}", ""]
        lines.append("### Wichtigste Notizen")
        for n in data["notes"][:20]:
            lines.append(f"- [[{n}]]")
        lines.append("")
        lines.append("### Häufige Tags")
        for tag, count in data["tags"].most_common(10):
            lines.append(f"- #{tag}: {count}")
        lines.append("")
        lines.append("### Häufige Beziehungen")
        for link, count in data["links"].most_common(10):
            lines.append(f"- [[{link}]]: {count}")
        lines.append("")
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
