from pathlib import Path
from .utils import now_date

def write_recommendations(settings: dict) -> Path:
    vault = Path(settings["vault_path"])
    folder = settings.get("vault_folders", {}).get("recommendations", "09_Recommendations")
    target_dir = vault / folder
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{now_date()}_recommendations.md"

    project_count = len(list((vault / settings.get("vault_folders", {}).get("projects", "01_Projekte")).glob("*.md"))) if (vault / settings.get("vault_folders", {}).get("projects", "01_Projekte")).exists() else 0
    task_count = len(list((vault / settings.get("vault_folders", {}).get("tasks", "04_Tasks")).glob("*.md"))) if (vault / settings.get("vault_folders", {}).get("tasks", "04_Tasks")).exists() else 0

    lines = [
        f"# Empfehlungen {now_date()}",
        "",
        "## Systemische Hinweise",
        "",
        f"- Projekte im Vault: {project_count}",
        f"- Aufgaben im Vault: {task_count}",
        "",
        "## Empfohlene Aktionen",
        "",
        "- Review Queue prüfen.",
        "- Inbox leeren.",
        "- Aufgaben ohne Projektbezug prüfen.",
        "- Graph-Index aktualisieren.",
        "- Quellen mit fehlenden Tags nachbearbeiten.",
    ]
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
