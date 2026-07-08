from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from secondbrain.backup import create_backup

if __name__ == "__main__":
    target = create_backup(PROJECT_ROOT)
    print(f"Backup erstellt: {target}")
