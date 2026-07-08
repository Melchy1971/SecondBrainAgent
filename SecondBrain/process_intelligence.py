from pathlib import Path
from collections import Counter
from .utils import now_date
from .vault_scan import iter_markdown, read_note

SYSTEM_KEYWORDS = ["sap", "p01", "p02", "pfs", "crm", "ctam", "cpq", "dive", "focused insights", "mcp", "obsidian"]

def write_process_map(settings: dict) -> Path:
    vault = Path(settings["vault_path"])
    folder = vault / settings.get("vault_folders", {}).get("processes", "15_Prozesse")
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"{now_date()}_prozesslandkarte.md"

    hits = Counter()
    sources = {k: [] for k in SYSTEM_KEYWORDS}
    for note in iter_markdown(vault):
        text = read_note(note).lower()
        for key in SYSTEM_KEYWORDS:
            if key in text:
                hits[key] += text.count(key)
                sources[key].append(note.stem)

    lines = ["# Prozesslandkarte", "", f"Datum: {now_date()}", "", "| System/Begriff | Gewicht | Quellen |", "|---|---:|---|"]
    for key, count in hits.most_common():
        linked = ", ".join(f"[[{s}]]" for s in sources[key][:5])
        lines.append(f"| {key} | {count} | {linked} |")
    if not hits:
        lines.append("| Keine Prozesssignale erkannt | 0 | - |")

    target.write_text("\n".join(lines), encoding="utf-8")
    return target
