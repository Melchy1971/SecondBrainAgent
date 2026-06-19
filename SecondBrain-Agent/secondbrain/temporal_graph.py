from pathlib import Path
import re
from .utils import now_date
from .vault_scan import iter_markdown, read_note

DATE_RE = re.compile(r"\b(20\d{2}-\d{2}-\d{2}|\d{2}\.\d{2}\.20\d{2})\b")

def build_temporal_graph(settings: dict) -> Path:
    vault = Path(settings["vault_path"])
    folder = vault / "23_TemporalGraph"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / "Temporal_Graph.md"

    events = []
    for note in iter_markdown(vault):
        text = read_note(note)
        found = DATE_RE.findall(text)
        for d in found[:10]:
            events.append((d, note.stem))

    lines = ["# Temporal Knowledge Graph", "", f"Aktualisiert: {now_date()}", "", "| Datum | Notiz |", "|---|---|"]
    if not events:
        lines.append("| keine Datumswerte erkannt | - |")
    for d, note in sorted(events):
        lines.append(f"| {d} | [[{note}]] |")
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
