from pathlib import Path
from .utils import now_date

AREAS = ["Beruf", "Privat", "Gesundheit", "Finanzen", "Lernen", "Reisen", "Verein", "Smart Home", "Projekte", "Wissen"]

def write_life_os_dashboard(settings: dict) -> Path:
    vault = Path(settings["vault_path"])
    folder = vault / "47_LifeOS"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"{now_date()}_life-os-dashboard.md"

    lines = ["# Life OS Dashboard", "", f"Datum: {now_date()}", "", "| Bereich | Status | Fokus |", "|---|---|---|"]
    for area in AREAS:
        lines.append(f"| {area} | aktiv | Review prüfen |")
    lines += ["", "## Morgenroutine", "", "- Chief of Staff prüfen", "- Projektstatus prüfen", "- Risiken prüfen", "- Tagesziele definieren"]
    lines += ["", "## Abendreview", "", "- Fortschritt prüfen", "- offene Punkte sichern", "- Morgen vorbereiten"]
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
