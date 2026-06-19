from pathlib import Path
from .utils import now_date

def update_graph(settings: dict, imported_items: list[dict]) -> Path | None:
    if not settings.get("graph_enabled", True):
        return None

    vault = Path(settings["vault_path"])
    graph_folder = settings.get("vault_folders", {}).get("graph", "07_Graph")
    target_dir = vault / graph_folder
    target_dir.mkdir(parents=True, exist_ok=True)

    target = target_dir / "Index.md"
    existing = ""
    if target.exists():
        existing = target.read_text(encoding="utf-8")

    lines = [existing.rstrip(), "", f"## Import {now_date()}", ""]
    if not imported_items:
        lines.append("- Keine neuen Knoten.")
    for item in imported_items:
        lines.append(f"- [[{Path(item['target']).stem}]] — {item['type']} / {item['provider']}")
    target.write_text("\n".join(lines).lstrip(), encoding="utf-8")
    return target
