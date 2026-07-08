from pathlib import Path
from .v98_common import VAULT, now_date, ensure

def read_optional(path: Path, limit: int = 4000) -> str:
    if not path.exists():
        return "Nicht vorhanden."
    return path.read_text(encoding="utf-8", errors="ignore")[:limit]

def write_chief_of_staff(vault: Path = VAULT) -> Path:
    target = ensure(vault / "112_ChiefOfStaff") / f"{now_date()}_chief-of-staff-v98.md"
    sources = [
        vault / "104_DailyAssistant" / f"{now_date()}_daily-assistant.md",
        vault / "106_TaskAgent" / f"{now_date()}_task-agent.md",
        vault / "109_ProjectAgent" / f"{now_date()}_project-agent.md",
        vault / "110_DecisionAgent" / f"{now_date()}_decision-agent.md",
        vault / "111_ProcessAgent" / f"{now_date()}_process-agent.md",
    ]
    lines = ["# Chief of Staff v9.8", "", f"Datum: {now_date()}", "", "## Lagebild", ""]
    for src in sources:
        lines.append(f"### {src.stem}")
        lines.append("")
        lines.append(read_optional(src, 2500))
        lines.append("")
    lines += ["## Priorisierte Tagesentscheidung", "", "- Risiken > offene Entscheidungen > blockierte Projekte > Aufgaben ohne Zielbezug.", "", "## Nächste Schritte", "", "- Top-3 Risiken prüfen.", "- Top-3 Aufgaben priorisieren.", "- Entscheidungen mit fehlenden Feldern ergänzen."]
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
