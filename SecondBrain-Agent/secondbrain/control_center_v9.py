from pathlib import Path
from .v9_common import now_date, ensure

def write_control_center(vault: Path) -> Path:
    folder = ensure(vault / "87_ControlCenter")
    target = folder / "SecondBrain_OS_Control_Center.md"
    modules = [
        "Workflow Engine",
        "Recommendation Engine",
        "Learning Engine",
        "Simulation Engine",
        "Personal CRM",
        "Executive Dashboard",
        "Voice Assistant",
        "API Gateway",
        "Monitoring & Telemetry",
        "Plugin Ecosystem",
        "Digital Twin v6",
    ]
    lines = ["# SecondBrain OS Control Center v9", "", f"Aktualisiert: {now_date()}", "", "| Modul | Status | Aktion |", "|---|---|---|"]
    for m in modules:
        lines.append(f"| {m} | aktiv/vorbereitet | prüfen |")
    lines += ["", "## Tagesroutine", "", "1. Import AI Exports", "2. SecondBrain OS Cycle", "3. v9 Cycle", "4. Dashboard prüfen", "5. Empfehlungen bearbeiten"]
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
