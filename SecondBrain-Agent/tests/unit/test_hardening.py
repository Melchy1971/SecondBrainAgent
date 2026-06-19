from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from secondbrain.hardening import hardening_score

if __name__ == "__main__":
    result = hardening_score(PROJECT_ROOT)
    assert result["total"] > 0
    assert "score" in result
    print("Hardening Test OK")
