from pathlib import Path
from .utils import now_date
import re

DATE_RE = re.compile(r"\b(20\d{2}-\d{2}-\d{2}|\d{2}\.\d{2}\.20\d{2})\b")

def import_ics(settings: dict, ics_path: str) -> Path:
    source = Path(ics_path)
    vault = Path(settings["vault_path"])
    folder = vault / "70_CalendarIntelligence"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"{now_date()}_ics-import.md"
    text = source.read_text(encoding="utf-8", errors="ignore")
    events = []
    current = {}
    for line in text.splitlines():
        if line.startswith("BEGIN:VEVENT"):
            current = {}
        elif line.startswith("SUMMARY:"):
            current["summary"] = line.split(":",1)[1]
        elif line.startswith("DTSTART"):
            current["start"] = line.split(":",1)[-1]
        elif line.startswith("END:VEVENT"):
            events.append(current)
    lines = ["# ICS Import", "", f"Quelle: `{source}`", "", "| Start | Termin |", "|---|---|"]
    for e in events:
        lines.append(f"| {e.get('start','')} | {e.get('summary','')} |")
    target.write_text("\n".join(lines), encoding="utf-8")
    return target

def write_calendar_intelligence(settings: dict) -> Path:
    vault = Path(settings["vault_path"])
    folder = vault / "70_CalendarIntelligence"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"{now_date()}_calendar-intelligence.md"
    lines = [
        "# Calendar Intelligence",
        "",
        f"Datum: {now_date()}",
        "",
        "## Status",
        "",
        "- Google Calendar: vorbereitet",
        "- Outlook Calendar: vorbereitet",
        "- ICS Import: verfügbar",
        "",
        "## Funktionen",
        "",
        "- Meeting-Vorbereitung",
        "- Nachbereitung",
        "- Tagesplanung",
        "- Wochenplanung",
        "- Fokuszeiten",
    ]
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
