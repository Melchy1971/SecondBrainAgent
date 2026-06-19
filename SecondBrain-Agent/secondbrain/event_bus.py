from pathlib import Path
import json
from .utils import now_date, now_datetime

def emit_event(settings: dict, event_type: str, payload: dict) -> Path:
    vault = Path(settings["vault_path"])
    folder = vault / "99_System" / "events"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"{now_date()}_events.jsonl"
    event = {
        "time": now_datetime(),
        "type": event_type,
        "payload": payload
    }
    with target.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
    return target

def write_event_summary(settings: dict) -> Path:
    vault = Path(settings["vault_path"])
    source_dir = vault / "99_System" / "events"
    folder = vault / "36_EventBus"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"{now_date()}_event-summary.md"

    counts = {}
    if source_dir.exists():
        for f in source_dir.glob("*.jsonl"):
            for line in f.read_text(encoding="utf-8").splitlines():
                try:
                    evt = json.loads(line)
                    counts[evt.get("type", "unknown")] = counts.get(evt.get("type", "unknown"), 0) + 1
                except Exception:
                    pass

    lines = ["# Event Summary", "", f"Datum: {now_date()}", "", "| Event | Anzahl |", "|---|---:|"]
    if not counts:
        lines.append("| keine | 0 |")
    for k, v in sorted(counts.items()):
        lines.append(f"| {k} | {v} |")
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
