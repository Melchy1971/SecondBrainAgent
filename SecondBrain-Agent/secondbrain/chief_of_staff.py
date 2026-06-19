from pathlib import Path
from .utils import now_date

def write_chief_of_staff_report(settings: dict) -> Path:
    vault = Path(settings["vault_path"])
    folder = vault / "18_AgentOps"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"{now_date()}_chief-of-staff.md"

    lines = [
        f"# Chief of Staff Report {now_date()}",
        "",
        "## Priorität 1",
        "",
        "- Daily Briefing prüfen",
        "- offene Aufgaben priorisieren",
        "- Projektmonitor prüfen",
        "",
        "## Priorität 2",
        "",
        "- Wissenslücken bewerten",
        "- Entscheidungen dokumentieren",
        "- Review Queue bereinigen",
        "",
        "## Systemstatus",
        "",
        "- Agent arbeitet Markdown-only.",
        "- Autonomie Level 5 ist strukturell vorbereitet.",
        "- Externe Aktionen bleiben ohne explizite Connector-Implementierung deaktiviert."
    ]
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
