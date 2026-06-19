from pathlib import Path
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    test = PROJECT_ROOT / "tests" / "test_smoke.py"
    result = subprocess.run([sys.executable, str(test)], cwd=str(PROJECT_ROOT))
    raise SystemExit(result.returncode)
