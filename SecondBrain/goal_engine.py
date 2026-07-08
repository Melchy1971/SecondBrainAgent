from pathlib import Path
from .utils import now_date
from .config import load_simple_yaml

def write_goal_map(project_root: Path, settings: dict) -> Path:
    vault = Path(settings["vault_path"])
    folder = vault / "50_Goals"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / "Goal_Map.md"
    goals = load_simple_yaml(project_root / "config" / "goals.yaml").get("goals", {})
    lines = ["# Goal Map", "", f"Aktualisiert: {now_date()}", "", "| Ziel | Bereich | Status | Ableitung |", "|---|---|---|---|"]
    if isinstance(goals, list):
        for g in goals:
            lines.append(f"| {g.get('title')} | {g.get('area')} | {g.get('status')} | Projekt → Tasks → Termine |")
    else:
        lines.append("| Keine Ziele geladen | - | - | - |")
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
