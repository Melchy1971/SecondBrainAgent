from pathlib import Path
from .utils import now_date

def write_process_copilot_templates(settings: dict) -> Path:
    vault = Path(settings["vault_path"])
    folder = vault / "31_ProcessCopilot"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / "Process_Copilot_Commands.md"

    lines = [
        "# Process Copilot Commands",
        "",
        f"Aktualisiert: {now_date()}",
        "",
        "## Kommandos",
        "",
        "- Erstelle Prozessdokumentation aus Quelle X.",
        "- Erstelle Swimlane für Prozess X.",
        "- Erstelle RACI für Prozess X.",
        "- Erstelle Testfälle für Prozess X.",
        "- Erstelle Management-OnePager für Prozess X.",
        "- Erstelle User Stories für Prozess X.",
    ]
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
