from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from secondbrain.backup_restore_test import run_backup_restore_test

if __name__ == "__main__":
    result = run_backup_restore_test(PROJECT_ROOT)
    assert result["ok"]
    print("Backup Restore Integration Test OK")
