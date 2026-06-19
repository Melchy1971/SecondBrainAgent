from pathlib import Path
from datetime import datetime

VAULT = Path(r"H:\SecondBrainAgent\SecondBrain")

def write_connector_status() -> Path:
    target = VAULT / "129_ConnectorFoundation" / "Connector_Foundation_Status.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Connector Foundation v10.1",
        "",
        f"Aktualisiert: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "| Connector | Status | Schreibzugriff | Bemerkung |",
        "|---|---|---|---|",
        "| ChatGPT Export | aktiv | nein | ZIP Import |",
        "| Gemini Export | aktiv | nein | ZIP Import |",
        "| Perplexity Export | aktiv | nein | ZIP Import |",
        "| Gmail | vorbereitet | nein | Import/Analyse geplant |",
        "| Outlook | vorbereitet | nein | Import/Analyse geplant |",
        "| IMAP | vorbereitet | nein | Import/Analyse geplant |",
        "| Google Calendar | vorbereitet | nein | Read-first |",
        "| Outlook Calendar | vorbereitet | nein | Read-first |",
        "| Browser | vorbereitet | nein | Bookmarks/Tabs später |",
        "| Git Repository | vorbereitet | nein | Read-only Import |",
    ]
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
