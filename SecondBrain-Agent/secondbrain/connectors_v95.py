from pathlib import Path
from datetime import datetime

VAULT = Path(r"H:\SecondBrainAgent\SecondBrain")

def write_calendar_status() -> Path:
    target = VAULT / "90_CalendarOps" / "Calendar_Connector_Status.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("""# Calendar Connectors

Status:
- ICS Import: aktiv/vorhanden
- Google Calendar: vorbereitet
- Outlook Calendar: vorbereitet

Sicherheitsregel:
- Keine Termine automatisch erstellen oder löschen.
""", encoding="utf-8")
    return target

def write_email_status() -> Path:
    target = VAULT / "91_EmailOps" / "Email_Connector_Status.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("""# Email Connectors

Status:
- Gmail: vorbereitet
- Outlook: vorbereitet
- IMAP: vorbereitet
- Senden: deaktiviert

Sicherheitsregel:
- Nur Import und Analyse. Kein automatischer Versand.
""", encoding="utf-8")
    return target
