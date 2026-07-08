from pathlib import Path
from datetime import datetime
import json

EVENT_FILE = Path(r"H:\SecondBrainAgent\SecondBrain-Agent\events\event_bus.jsonl")
VAULT = Path(r"H:\SecondBrainAgent\SecondBrain")

def emit(event_type: str, payload: dict) -> None:
    EVENT_FILE.parent.mkdir(parents=True, exist_ok=True)
    event = {"time": datetime.now().isoformat(timespec="seconds"), "type": event_type, "payload": payload}
    with EVENT_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")

def read_events(limit: int = 100) -> list[dict]:
    if not EVENT_FILE.exists():
        return []
    rows = EVENT_FILE.read_text(encoding="utf-8", errors="ignore").splitlines()[-limit:]
    out = []
    for r in rows:
        try:
            out.append(json.loads(r))
        except Exception:
            pass
    return out

def write_event_summary() -> Path:
    target = VAULT / "93_RealtimeEventBus" / f"{datetime.now().strftime('%Y-%m-%d')}_event-bus.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    events = read_events(200)
    lines = ["# Realtime Event Bus", "", f"Events: {len(events)}", "", "| Zeit | Typ | Payload |", "|---|---|---|"]
    for e in events[-100:]:
        lines.append(f"| {e.get('time')} | {e.get('type')} | `{e.get('payload')}` |")
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
