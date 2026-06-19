from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from secondbrain.config import load_settings
from secondbrain.backup_restore_test import write_backup_restore_test_report, run_backup_restore_test

if __name__ == "__main__":
    settings = load_settings(PROJECT_ROOT)
    target = write_backup_restore_test_report(PROJECT_ROOT, settings)
    result = run_backup_restore_test(PROJECT_ROOT)
    print(f"Backup Restore Test: {'PASS' if result['ok'] else 'FAIL'}")
    print(f"Report: {target}")
    raise SystemExit(0 if result["ok"] else 2)
