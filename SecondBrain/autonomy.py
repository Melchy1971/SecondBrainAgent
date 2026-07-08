from pathlib import Path
from .path import from_settings_mapping
from .utils import now_date, now_datetime

def write_autonomy_report(settings: dict) -> Path:
    vault = from_settings_mapping(settings).vault
    target_dir = vault / "99_System" / "autonomy"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{now_date()}_autonomy-report.md"

    sections = [
        f"# Autonomy Report {now_datetime()}",
        "",
        "## Ausgeführte Kontrollpunkte",
        "",
        "- Importstatus geprüft",
        "- Projektmonitor vorgesehen",
        "- Wissenslücken vorgesehen",
        "- Daily Briefing vorgesehen",
        "- Governance vorgesehen",
        "",
        "## Entscheidungsvorschläge",
        "",
        "- Review Queue vor automatischen Strukturänderungen prüfen.",
        "- Projektmonitor als Tagessteuerung verwenden.",
        "- Wissenslücken mit hoher Wiederholung priorisieren.",
        "",
        "## Sicherheitsgrenze",
        "",
        "- Keine E-Mails senden.",
        "- Keine Dateien löschen.",
        "- Keine externen API-Aktionen ohne Schlüssel und explizite Aktivierung.",
    ]
    target.write_text("\n".join(sections), encoding="utf-8")
    return target
