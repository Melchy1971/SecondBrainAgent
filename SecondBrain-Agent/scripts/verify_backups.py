from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from secondbrain.config import load_settings
from secondbrain.backup_verification import verify_backups

if __name__ == "__main__":
    settings = load_settings(PROJECT_ROOT)
    target = verify_backups(PROJECT_ROOT, settings)
    print(f"Backup-Verifikation erstellt: {target}")
