from pathlib import Path
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]

tests = [
    PROJECT_ROOT / "tests" / "unit" / "test_hardening.py",
    PROJECT_ROOT / "tests" / "unit" / "test_safe_logging.py",
    PROJECT_ROOT / "tests" / "integration" / "test_backup_restore.py",
]

if __name__ == "__main__":
    failed = 0
    for test in tests:
        print(f"Run {test}")
        result = subprocess.run([sys.executable, str(test)], cwd=str(PROJECT_ROOT))
        if result.returncode != 0:
            failed += 1
    raise SystemExit(1 if failed else 0)
