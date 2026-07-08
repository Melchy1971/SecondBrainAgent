from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from secondbrain.production_ready_v96 import run_production_ready_gate, write_production_ready_gate
if __name__ == "__main__":
    result = run_production_ready_gate()
    report = write_production_ready_gate()
    print(f"Production Ready Gate v9.6: {result['status']} ({result['score']})")
    print(report)
    raise SystemExit(0 if result["status"] == "PASS" else 2)
