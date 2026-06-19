from pathlib import Path
from .v9_common import now_date, ensure

def write_voice_assistant_status(vault: Path) -> Path:
    folder = ensure(vault / "82_VoiceAssistant")
    target = folder / "Voice_Assistant_Status.md"
    lines = [
        "# Voice Assistant",
        "",
        f"Aktualisiert: {now_date()}",
        "",
        "## Status",
        "",
        "- Spracheingabe: vorbereitet",
        "- Textkommandos: aktiv",
        "- Lokale Spracherkennung: optional",
        "",
        "## Beispielkommandos",
        "",
        "- Zeige Projekt Wissensdatenbank.",
        "- Welche Risiken gibt es?",
        "- Fasse die Woche zusammen.",
        "- Welche Entscheidungen fehlen?",
    ]
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
