from pathlib import Path
from collections import defaultdict
from .v99_common import VAULT, iter_notes, read, now_date, ensure

DONE = ["abgeschlossen", "erledigt", "fertig", "pass", "done"]
OPEN = ["offen", "todo", "geplant", "blocked", "blockiert", "fail", "nicht fertig"]

def normalize_topic(stem: str) -> str:
    s = stem.lower()
    for token in ["status", "report", "review", "dashboard", "index"]:
        s = s.replace(token, "")
    return s.strip("_- ")

def detect_status(text: str):
    low = text.lower()
    has_done = any(k in low for k in DONE)
    has_open = any(k in low for k in OPEN)
    if has_done and has_open:
        return "mixed"
    if has_done:
        return "done"
    if has_open:
        return "open"
    return "unknown"

def write_contradictions(vault: Path = VAULT) -> Path:
    target = ensure(vault / "116_ContradictionDetection") / f"{now_date()}_contradictions.md"
    topic_status = defaultdict(list)
    mixed_notes = []

    for p in iter_notes(vault):
        text = read(p)
        status = detect_status(text)
        topic = normalize_topic(p.stem)
        topic_status[topic].append((status, p.stem))
        if status == "mixed":
            mixed_notes.append(p.stem)

    contradictions = []
    for topic, rows in topic_status.items():
        statuses = set(s for s, _ in rows if s != "unknown")
        if "done" in statuses and "open" in statuses:
            contradictions.append((topic, rows))

    lines = ["# Contradiction Detection v9.9", "", f"Datum: {now_date()}", "", "## Direkte Mischsignale", ""]
    if mixed_notes:
        for stem in mixed_notes[:100]:
            lines.append(f"- [[{stem}]] enthält erledigt/offen-Signale")
    else:
        lines.append("- Keine.")
    lines += ["", "## Themen-Widersprüche", ""]
    if contradictions:
        for topic, rows in contradictions[:80]:
            linked = ", ".join(f"[[{stem}]] ({status})" for status, stem in rows[:10])
            lines.append(f"- **{topic}**: {linked}")
    else:
        lines.append("- Keine starken Widersprüche erkannt.")
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
