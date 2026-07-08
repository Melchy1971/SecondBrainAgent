from pathlib import Path
from .utils import now_date

PROJECTS = ["Wissensdatenbank", "Jarvis", "SecondBrain", "Tischtennis-Buddy"]

def write_software_factory(settings: dict) -> Path:
    vault = Path(settings["vault_path"])
    folder = vault / "62_SoftwareFactory"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"{now_date()}_software-factory.md"
    lines = ["# Autonomous Software Factory", "", f"Datum: {now_date()}", "", "| Projekt | Pipeline | Status |", "|---|---|---|"]
    for p in PROJECTS:
        lines.append(f"| {p} | Anforderungen → Architektur → Code → Tests → Doku → Deployment | vorbereitet |")
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
