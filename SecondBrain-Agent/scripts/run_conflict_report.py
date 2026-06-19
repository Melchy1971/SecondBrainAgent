from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from secondbrain.config import load_settings
from secondbrain.conflicts import write_conflict_report

if __name__ == "__main__":
    settings = load_settings(PROJECT_ROOT)
    target = write_conflict_report(settings)
    print(f"Conflict Report erstellt: {target}")
