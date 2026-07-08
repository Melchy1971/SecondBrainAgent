from pathlib import Path
from .utils import now_date

def write_research_backlog(settings: dict) -> Path:
    vault = Path(settings["vault_path"])
    gap_folder = vault / "20_KnowledgeGaps"
    folder = vault / "27_Research"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"{now_date()}_research-backlog.md"

    lines = ["# Research Backlog", "", f"Datum: {now_date()}", "", "## Rechercheaufträge", ""]
    gaps = list(gap_folder.glob("*.md")) if gap_folder.exists() else []
    if not gaps:
        lines.append("- Keine Wissenslücken-Datei gefunden.")
    else:
        for g in gaps[-5:]:
            lines.append(f"- [[{g.stem}]] prüfen und Quellen ergänzen.")
    lines += ["", "## Sicherheitsregel", "", "- Web-Recherche nur explizit oder über freigegebenen Connector ausführen."]
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
