from pathlib import Path
from .utils import now_date

AGENTS = ["Importer", "Review", "Project", "Research", "Process", "Governance", "Quality", "Executive"]

def write_agent_economy_report(settings: dict) -> Path:
    vault = Path(settings["vault_path"])
    folder = vault / "42_AgentEconomy"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"{now_date()}_agent-economy.md"

    lines = ["# Agent Economy", "", f"Datum: {now_date()}", "", "| Agent | Kosten | Laufzeit | Nutzen | Status |", "|---|---:|---:|---:|---|"]
    for a in AGENTS:
        lines.append(f"| {a} | 0 | 0 | offen | vorbereitet |")
    lines += ["", "## Ziel", "", "- Token, Laufzeit, Erfolgsquote und Nutzen je Agent messen."]
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
