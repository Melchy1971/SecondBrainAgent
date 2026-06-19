from pathlib import Path
from .v10_common import VAULT, now_date, ensure

def write_command_center(vault: Path = VAULT) -> Path:
    target = ensure(vault / "126_CommandCenter") / "SecondBrain_Command_Center_v10.md"
    modules = [
        "Life Dashboard",
        "Daily OS",
        "Weekly OS",
        "Personal KPIs",
        "Personal ERP",
        "Jarvis Copilot",
        "Knowledge Intelligence",
        "Agentic Work",
        "AI Copilot",
        "RAG",
    ]
    lines = ["# SecondBrain Command Center v10", "", f"Aktualisiert: {now_date()}", "", "| Modul | Status | Aktion |", "|---|---|---|"]
    for m in modules:
        lines.append(f"| {m} | aktiv | prüfen |")
    lines += ["", "## Tagesroutine", "", "1. Import AI Exports", "2. v10 Cycle", "3. Daily OS prüfen", "4. Jarvis Copilot lesen", "5. Top-3 Aktionen bearbeiten"]
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
