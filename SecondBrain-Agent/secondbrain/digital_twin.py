from pathlib import Path
from collections import Counter
from .utils import now_date
from .vault_scan import iter_markdown, read_note

def write_digital_twin_profile(settings: dict) -> Path:
    vault = Path(settings["vault_path"])
    folder = vault / settings.get("vault_folders", {}).get("digital_twin", "17_DigitalTwin")
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / "Digital_Twin_Profile.md"

    terms = Counter()
    for note in iter_markdown(vault):
        text = read_note(note).lower()
        for key in ["prozess", "projekt", "obsidian", "claude", "python", "tischtennis", "sap", "automation", "wissen"]:
            if key in text:
                terms[key] += text.count(key)

    lines = ["# Digital Twin Profile", "", f"Aktualisiert: {now_date()}", "", "## Arbeitsmuster", ""]
    for key, count in terms.most_common():
        lines.append(f"- {key}: {count}")
    lines += ["", "## Ableitungen", "", "- Bevorzugt strukturierte Systeme.", "- Nutzt Obsidian als Markdown-Wissensbasis.", "- Priorisiert Automatisierung und Prozesslogik."]
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
