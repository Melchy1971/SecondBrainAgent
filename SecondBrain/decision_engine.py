from pathlib import Path
import re
from .utils import now_date, slugify, ensure_unique_path
from .vault_scan import iter_markdown, read_note

MARKERS = ["entscheidung:", "beschluss:", "festlegung:", "decision:"]

def extract_decisions_from_text(text: str) -> list[str]:
    out = []
    for line in text.splitlines():
        low = line.lower().strip()
        for marker in MARKERS:
            if marker in low:
                value = line.split(":", 1)[-1].strip()
                if value:
                    out.append(value)
    return out

def write_decision_register(settings: dict) -> Path:
    vault = Path(settings["vault_path"])
    folder = vault / settings.get("vault_folders", {}).get("decisions", "12_Decisions")
    folder.mkdir(parents=True, exist_ok=True)
    register = folder / "Decision_Register.md"

    decisions = []
    for note in iter_markdown(vault):
        text = read_note(note)
        for decision in extract_decisions_from_text(text):
            decisions.append((decision, note.stem))

    lines = ["# Decision Register", "", f"Aktualisiert: {now_date()}", "", "| Entscheidung | Quelle |", "|---|---|"]
    if not decisions:
        lines.append("| Keine Entscheidungen erkannt | - |")
    for decision, source in decisions:
        lines.append(f"| {decision} | [[{source}]] |")
    register.write_text("\n".join(lines), encoding="utf-8")
    return register
