from pathlib import Path
from .utils import now_date

def write_twin_reports(settings: dict) -> list[Path]:
    vault = Path(settings["vault_path"])
    specs = {
        "56_DigitalTwinV4/Digital_Twin_v4.md": [
            "# Digital Twin v4",
            "## Kennt",
            "- Arbeitsmuster",
            "- Lernmuster",
            "- Entscheidungen",
            "- Gesundheit",
            "- Kommunikation",
            "- Prioritäten",
            "- Produktivität",
        ],
        "57_ProcessTwin/Process_Twin.md": [
            "# Process Twin",
            "## Erzeugt",
            "- Prozesslandkarte",
            "- BPMN",
            "- RACI",
            "- Systemlandkarte",
            "- KPIs",
            "- Risiken",
        ],
        "58_KnowledgeTwin/Knowledge_Twin.md": [
            "# Knowledge Twin",
            "## Bewertet",
            "- vorhandenes Wissen",
            "- fehlendes Wissen",
            "- veraltetes Wissen",
            "- kritisches Wissen",
        ],
    }
    created = []
    for rel, lines in specs.items():
        target = vault / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("\n\n".join(lines) + f"\n\nAktualisiert: {now_date()}\n", encoding="utf-8")
        created.append(target)
    return created
