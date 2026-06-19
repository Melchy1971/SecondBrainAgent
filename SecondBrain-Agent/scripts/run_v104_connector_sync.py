from pathlib import Path
import json
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from secondbrain.connector_runtime_v104 import registry_from_config, sync_all
from secondbrain.runtime_events_v104 import JsonlEventStore


def main() -> int:
    cfg = json.loads((PROJECT_ROOT / "config" / "connectors_v104.json").read_text(encoding="utf-8"))
    registry = registry_from_config(PROJECT_ROOT, cfg)
    store = JsonlEventStore(PROJECT_ROOT / "events" / "runtime")
    results = sync_all(registry, store)
    for result in results:
        print(f"{result.connector}: fetched={result.fetched} normalized={result.normalized} errors={len(result.errors)}")
        for error in result.errors:
            print(f"  - {error}")
    summary = store.summarize()
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if all(not result.errors for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
