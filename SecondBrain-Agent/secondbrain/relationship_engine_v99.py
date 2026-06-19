from pathlib import Path
import json
from collections import Counter
from .v99_common import VAULT, iter_notes, read, links, tags, source_of, now_date, ensure

def edge_type(text: str, target: str) -> str:
    low = text.lower()
    if "blockiert" in low or "blocked" in low:
        return "blocks"
    if "entscheidung" in low or "beschluss" in low:
        return "decides"
    if "risiko" in low:
        return "influences"
    if "- [ ]" in text:
        return "creates_task"
    if "quelle" in low:
        return "references"
    return "mentions"

def build_relationships(vault: Path = VAULT) -> Path:
    system = ensure(vault / "99_System" / "relationships")
    out_json = system / "relationships.json"
    edges = []
    counts = Counter()

    for p in iter_notes(vault):
        text = read(p)
        src = source_of(text, p)
        for link in links(text):
            target = link.split("|")[0].split("#")[0]
            typ = edge_type(text, target)
            edges.append({"source": p.stem, "target": target, "type": typ, "source_origin": src, "weight": 1})
            counts[typ] += 1
        for tag in tags(text):
            edges.append({"source": p.stem, "target": f"#{tag}", "type": "tagged_as", "source_origin": src, "weight": 1})
            counts["tagged_as"] += 1

    out_json.write_text(json.dumps(edges, ensure_ascii=False, indent=2), encoding="utf-8")
    report = ensure(vault / "114_RelationshipEngine") / "Relationship_Index.md"
    lines = ["# Relationship Engine v9.9", "", f"Aktualisiert: {now_date()}", "", "| Beziehung | Anzahl |", "|---|---:|"]
    for typ, count in counts.most_common():
        lines.append(f"| {typ} | {count} |")
    lines += ["", "## JSON", "", f"`{out_json}`"]
    report.write_text("\n".join(lines), encoding="utf-8")
    return report
