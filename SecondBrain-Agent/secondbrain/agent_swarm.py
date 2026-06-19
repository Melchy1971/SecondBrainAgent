from pathlib import Path
from .utils import now_date

AGENTS = ["Supervisor", "Research", "Project", "Meeting", "Process", "Knowledge", "Governance", "Quality", "Executive"]

def write_agent_swarm_status(settings: dict) -> Path:
    vault = Path(settings["vault_path"])
    folder = vault / "34_AgentSwarm"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / "Agent_Swarm_Status.md"

    lines = ["# Agent Swarm Status", "", f"Aktualisiert: {now_date()}", "", "| Agent | Aufgabe | Status |", "|---|---|---|"]
    for agent in AGENTS:
        lines.append(f"| {agent} Agent | spezialisiert | vorbereitet |")
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
