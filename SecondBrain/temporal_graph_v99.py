from pathlib import Path
import json
from datetime import datetime
from collections import Counter
from .v99_common import VAULT, iter_notes, read, frontmatter_value, now_date, ensure, source_of

def parse_date(text: str, path: Path):
    val = frontmatter_value(text, "created")
    if val:
        return val[:10]
    try:
        return datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d")
    except Exception:
        return "unknown"

def build_temporal_graph(vault: Path = VAULT) -> Path:
    system = ensure(vault / "99_System" / "temporal_graph")
    out_json = system / "temporal_knowledge_graph.json"
    rows = []
    per_day = Counter()

    for p in iter_notes(vault):
        text = read(p)
        day = parse_date(text, p)
        src = source_of(text, p)
        rows.append({"date": day, "note": p.stem, "path": str(p), "source": src})
        per_day[day] += 1

    rows = sorted(rows, key=lambda x: x["date"])
    out_json.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    report = ensure(vault / "115_TemporalKnowledgeGraph") / "Temporal_Knowledge_Graph.md"
    lines = ["# Temporal Knowledge Graph v9.9", "", f"Aktualisiert: {now_date()}", "", "| Datum | Notizen |", "|---|---:|"]
    for day, count in sorted(per_day.items()):
        lines.append(f"| {day} | {count} |")
    report.write_text("\n".join(lines), encoding="utf-8")
    return report
