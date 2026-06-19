from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from secondbrain.diagnostics import write_diagnostics

if __name__ == "__main__":
    target = write_diagnostics(PROJECT_ROOT)
    print(f"Diagnose erstellt: {target}")
