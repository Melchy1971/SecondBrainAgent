from pathlib import Path
from .utils import now_date
from .vault_scan import iter_markdown, read_note, frontmatter_value

def build_lineage_index(settings: dict) -> Path:
    vault = Path(settings["vault_path"])
    folder = vault / "24_Lineage"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / "Knowledge_Lineage.md"

    lines = ["# Knowledge Lineage", "", f"Aktualisiert: {now_date()}", "", "| Notiz | Quelle | Provider |", "|---|---|---|"]
    count = 0
    for note in iter_markdown(vault):
        text = read_note(note)
        source = frontmatter_value(text, "source_file")
        provider = frontmatter_value(text, "provider")
        if source or provider:
            lines.append(f"| [[{note.stem}]] | `{source}` | `{provider}` |")
            count += 1
    if count == 0:
        lines.append("| Keine Lineage-Daten erkannt | - | - |")
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
