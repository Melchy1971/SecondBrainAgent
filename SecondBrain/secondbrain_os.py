from pathlib import Path
from .utils import now_date

def write_secondbrain_os_dashboard(settings: dict) -> Path:
    vault = Path(settings["vault_path"])
    folder = vault / "75_SecondBrainOS"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / "SecondBrain_OS_Dashboard.md"
    sections = [
        "Semantic Search",
        "Knowledge Graph",
        "Agent Memory",
        "Project Intelligence",
        "Decision Intelligence",
        "Meeting Intelligence",
        "Calendar Intelligence",
        "Data Warehouse",
        "MCP Ecosystem",
        "Digital Twin",
        "Self-Improving Knowledge",
    ]
    lines = ["# SecondBrain OS Dashboard", "", f"Aktualisiert: {now_date()}", "", "| Modul | Status |", "|---|---|"]
    for s in sections:
        lines.append(f"| {s} | aktiv/vorbereitet |")
    lines += ["", "## Nächste Betriebsroutine", "", "1. Import", "2. SecondBrain OS Cycle", "3. Quality Gate", "4. Review Queue", "5. Plugin prüfen"]
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
