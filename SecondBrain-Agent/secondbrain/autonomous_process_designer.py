from pathlib import Path
from .utils import now_date
from .vault_scan import iter_markdown, read_note

def write_process_design_backlog(settings: dict) -> Path:
    vault = Path(settings["vault_path"])
    folder = vault / "46_AutonomousProcessDesigner"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"{now_date()}_process-design-backlog.md"

    candidates = []
    for note in iter_markdown(vault):
        text = read_note(note).lower()
        if any(k in text for k in ["prozess", "freigabe", "genehmigung", "workflow", "schnittstelle", "kpi"]):
            candidates.append(note.stem)

    lines = ["# Autonomous Process Designer", "", f"Datum: {now_date()}", "", "## Prozesskandidaten", ""]
    lines += [f"- [[{c}]] → Prozessdokumentation / RACI / Testfälle prüfen" for c in candidates[:100]] or ["- Keine Prozesskandidaten."]
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
