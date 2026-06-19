from pathlib import Path
from datetime import datetime
import json

VAULT = Path(r"H:\SecondBrainAgent\SecondBrain")

DASHBOARDS = {
    "command_center": VAULT / "126_CommandCenter" / "SecondBrain_Command_Center_v10.md",
    "life": VAULT / "120_LifeDashboard" / "Life_Dashboard_v10.md",
    "knowledge": VAULT / "119_KnowledgeIntelligenceDashboard" / "Knowledge_Intelligence_Dashboard_v99.md",
    "v95": VAULT / "98_V95ControlCenter" / "SecondBrain_v9_5_Control_Center.md",
}

def write_dashboard_catalog() -> Path:
    target = VAULT / "131_DashboardAPI" / "Dashboard_Catalog.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Dashboard API v10.1", "", f"Aktualisiert: {datetime.now().strftime('%Y-%m-%d %H:%M')}", "", "| Name | Pfad | Status |", "|---|---|---|"]
    for name, path in DASHBOARDS.items():
        lines.append(f"| {name} | `{path}` | {'vorhanden' if path.exists() else 'fehlt'} |")
    target.write_text("\n".join(lines), encoding="utf-8")
    return target

def dashboard_json() -> dict:
    return {name: {"path": str(path), "exists": path.exists()} for name, path in DASHBOARDS.items()}
