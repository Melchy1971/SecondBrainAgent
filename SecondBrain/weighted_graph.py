from pathlib import Path
from collections import Counter
import re
from .utils import now_date

def extract_links(text: str) -> list[str]:
    return re.findall(r"\[\[([^\]]+)\]\]", text)

def update_weighted_graph(settings: dict) -> Path:
    vault = Path(settings["vault_path"])
    graph_folder = settings.get("vault_folders", {}).get("graph", "07_Graph")
    target_dir = vault / graph_folder / "Weights"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / "weighted_edges.md"

    edges = Counter()
    for note in vault.rglob("*.md"):
        if "99_System" in note.parts:
            continue
        try:
            text = note.read_text(encoding="utf-8")
        except Exception:
            continue
        source = note.stem
        for link in extract_links(text):
            edges[(source, link)] += 1

    lines = ["# Weighted Knowledge Graph", "", f"Aktualisiert: {now_date()}", "", "| Quelle | Ziel | Gewicht |", "|---|---|---|"]
    for (src, dst), weight in sorted(edges.items(), key=lambda x: (-x[1], x[0])):
        lines.append(f"| [[{src}]] | [[{dst}]] | {weight} |")

    target.write_text("\n".join(lines), encoding="utf-8")
    return target
