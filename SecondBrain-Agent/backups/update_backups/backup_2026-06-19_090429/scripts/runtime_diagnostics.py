from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from secondbrain.hardening import write_runtime_diagnostics, hardening_score

if __name__ == "__main__":
    target = write_runtime_diagnostics(PROJECT_ROOT)
    score = hardening_score(PROJECT_ROOT)
    print(f"Runtime Diagnostics: {target}")
    print(f"Hardening Score: {score['score']} ({score['passed']}/{score['total']})")
