from pathlib import Path
from .utils import now_date

def write_personal_agi_os(settings: dict) -> Path:
    vault = Path(settings["vault_path"])
    folder = vault / "64_PersonalAGIOS"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / "Personal_AGI_OS.md"
    lines = [
        "# Personal AGI Operating System",
        "",
        f"Aktualisiert: {now_date()}",
        "",
        "## Systembestandteile",
        "",
        "- Life OS",
        "- Chief of Staff",
        "- Digital Twin",
        "- Knowledge Twin",
        "- Process Twin",
        "- Enterprise RAG",
        "- Data Warehouse",
        "- Multi-Agent-Swarm",
        "- Local AI Cluster",
        "- Autonomous Software Factory",
        "",
        "## Sicherheitsgrenzen",
        "",
        "- keine destruktiven Aktionen",
        "- keine externen Aktionen ohne Freigabe",
        "- Markdown-first",
        "- Review-first",
    ]
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
