from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from secondbrain.restore import list_backups

if __name__ == "__main__":
    backups = list_backups(PROJECT_ROOT)
    if not backups:
        print("Keine Backups gefunden.")
    for b in backups:
        print(b)
