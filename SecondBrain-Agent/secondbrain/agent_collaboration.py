from pathlib import Path
from .utils import now_date

def write_collaboration_protocol(settings: dict) -> Path:
    vault = Path(settings["vault_path"])
    folder = vault / "49_AgentCollaboration"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / "Agent_Collaboration_Protocol.md"
    lines = [
        "# Agent Collaboration Protocol",
        "",
        f"Aktualisiert: {now_date()}",
        "",
        "## Pipeline",
        "",
        "Research Agent → Process Agent → Executive Agent → Chief of Staff",
        "",
        "## Delegationsregeln",
        "",
        "- Research Agent schließt Wissenslücken.",
        "- Project Agent bewertet Blocker und Deadlines.",
        "- Process Agent erzeugt Prozessartefakte.",
        "- Executive Agent verdichtet Managementsicht.",
        "- Chief of Staff priorisiert.",
        "",
        "## Konfliktlösung",
        "",
        "- Widersprüche als Review-Aufgabe markieren.",
        "- Keine automatische Löschung.",
        "- Entscheidungen ins Decision Journal schreiben."
    ]
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
