from pathlib import Path
import json
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from secondbrain.ai_runtime_v105 import build_context, load_model_router
from secondbrain.runtime_events_v104 import JsonlEventStore


def main() -> int:
    store = JsonlEventStore(PROJECT_ROOT / "events" / "runtime")
    records = [event.payload for event in store.filter(event_type="connector.record.normalized")]
    context = build_context(records)
    router = load_model_router(PROJECT_ROOT)
    answer = router.run("project_briefing", "Erstelle ein kurzes Lagebild aus diesem Kontext:\n\n" + context)
    target = PROJECT_ROOT / "events" / "ai_runtime_last_answer.md"
    target.write_text(answer, encoding="utf-8")
    print(answer)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
