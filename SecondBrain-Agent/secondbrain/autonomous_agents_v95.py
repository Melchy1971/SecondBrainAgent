from pathlib import Path
from datetime import datetime
from .event_bus_v95 import emit

VAULT = Path(r"H:\SecondBrainAgent\SecondBrain")

AGENTS = [
    "Research Agent",
    "Project Agent",
    "Meeting Agent",
    "Decision Agent",
    "Process Agent",
    "Executive Agent",
    "Chief of Staff Agent",
    "Learning Agent",
    "CRM Agent",
]

def write_agent_status() -> Path:
    target = VAULT / "94_AutonomousAgents" / "Autonomous_Agents_Status.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Autonomous Agents", "", f"Aktualisiert: {datetime.now().strftime('%Y-%m-%d %H:%M')}", "", "| Agent | Status | Autonomie |", "|---|---|---|"]
    for a in AGENTS:
        lines.append(f"| {a} | vorbereitet | review-first |")
    target.write_text("\n".join(lines), encoding="utf-8")
    emit("agents.status_written", {"agents": len(AGENTS)})
    return target
