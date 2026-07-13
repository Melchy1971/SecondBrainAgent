from pathlib import Path
import sys
import time

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from modules.orchestrator.orchestrator import run_once
from secondbrain.config import load_settings

if __name__ == "__main__":
    settings = load_settings(PROJECT_ROOT)
    interval = int(settings.get("watch_interval_seconds", 30))
    print(f"Watcher gestartet. Intervall: {interval} Sekunden. Abbruch: STRG+C")

    while True:
        imported = run_once(PROJECT_ROOT)
        if imported:
            print(f"Neue Dateien importiert: {len(imported)}")
        time.sleep(interval)
