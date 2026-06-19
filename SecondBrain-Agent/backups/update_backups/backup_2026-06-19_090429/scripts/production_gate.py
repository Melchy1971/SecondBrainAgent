from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from secondbrain.production_gate import write_production_gate_report, run_production_gate

if __name__ == "__main__":
    report = write_production_gate_report(PROJECT_ROOT)
    result = run_production_gate(PROJECT_ROOT)
    print(f"Production Gate: {result['status']} ({result['score']})")
    print(f"Report: {report}")
    raise SystemExit(0 if result["status"] == "PASS" else 2)
