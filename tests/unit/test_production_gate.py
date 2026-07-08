from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from secondbrain.production_gate import run_production_gate

if __name__ == "__main__":
    result = run_production_gate(PROJECT_ROOT)
    assert "score" in result
    assert "status" in result
    print("Production Gate Test OK")
