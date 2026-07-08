from pathlib import Path
from .utils import now_date
from .vault_scan import iter_markdown, read_note, note_type

def write_executive_dashboard(settings: dict) -> Path:
    vault = Path(settings["vault_path"])
    folder = vault / "32_ExecutiveDashboard"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / "Executive_Dashboard.md"

    counts = {}
    for note in iter_markdown(vault):
        t = note_type(read_note(note)) or "unknown"
        counts[t] = counts.get(t, 0) + 1

    lines = ["# Executive Dashboard", "", f"Aktualisiert: {now_date()}", "", "## KPIs", ""]
    for k, v in sorted(counts.items()):
        lines.append(f"- {k}: {v}")
    lines += ["", "## Führungsfragen", "", "- Was ist blockiert?", "- Welche Entscheidung fehlt?", "- Welche Projekte haben Risiken?", "- Welche Wissenslücken sind kritisch?"]
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
