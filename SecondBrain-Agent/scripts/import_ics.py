from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from secondbrain.config import load_settings
from secondbrain.calendar_intelligence import import_ics

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Nutzung: python scripts\\import_ics.py <calendar.ics>")
        raise SystemExit(1)
    settings = load_settings(PROJECT_ROOT)
    target = import_ics(settings, sys.argv[1])
    print(f"ICS importiert: {target}")
