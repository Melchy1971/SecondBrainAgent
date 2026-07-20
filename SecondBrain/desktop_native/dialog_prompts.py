from __future__ import annotations

from typing import Any, Mapping


_SLOT_PROMPTS = {
    "title": "Wie lautet der Titel?",
    "when": "Wann soll der Termin stattfinden?",
    "recipient": "Wer soll die E-Mail erhalten?",
    "body": "Wie lautet der Inhalt der E-Mail?",
    "path": "Welche Datei soll verwendet werden?",
    "query": "Wonach soll ich suchen?",
    "text": "Was möchtest du wissen?",
}


def dialog_prompt(result: Mapping[str, Any]) -> str | None:
    """Return a non-sensitive prompt for GUI and optional TTS presentation."""
    status = str(result.get("status") or "")
    if status == "slots_required":
        missing = result.get("missing") or []
        slot = str(missing[0]) if missing else ""
        return _SLOT_PROMPTS.get(slot, "Welche Angabe fehlt noch?")
    if status == "confirmation_required":
        return "Soll ich diese Aktion ausführen? Sage Ja zum Bestätigen oder Abbrechen."
    if status == "approval_required":
        return "Die Aktion wartet auf eine Freigabe im Approval Center."
    if status == "dialog_cancelled":
        return "Dialog abgebrochen."
    if status == "error" and result.get("error") == "slot_value_required":
        return "Bitte nenne zuerst die fehlende Angabe oder sage Abbrechen."
    return None
