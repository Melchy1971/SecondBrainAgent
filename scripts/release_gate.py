from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from secondbrain.release_gate import write_release_gate_report, run_release_gate

if __name__ == "__main__":
    target = write_release_gate_report(PROJECT_ROOT)
    result = run_release_gate(PROJECT_ROOT)
    print(f"Release Gate: {result['status']} ({result['score']}/100)")
    print(f"Report: {target}")
    raise SystemExit(0 if result["status"] == "PASS" else 2)
