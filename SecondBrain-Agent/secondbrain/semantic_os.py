from pathlib import Path
from .utils import now_date

def write_semantic_os_status(settings: dict) -> Path:
    vault = Path(settings["vault_path"])
    folder = vault / "60_SemanticOS"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / "Semantic_OS_Status.md"
    entities = ["Entitäten", "Beziehungen", "Ereignisse", "Ziele", "Entscheidungen"]
    lines = ["# Semantic Operating System", "", f"Aktualisiert: {now_date()}", ""]
    for e in entities:
        lines.append(f"- {e}: vorbereitet")
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
