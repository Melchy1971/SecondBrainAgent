"""P1 v19.6 - CLI for P1 maturity gate."""

from __future__ import annotations

import json
from pathlib import Path

from secondbrain.gates.p1_maturity_gate import P1MaturityGate


DEFAULT_CAPABILITIES = {
    "hybrid_retrieval": True,
    "rrf": True,
    "retrieval_kpis": True,
    "kpi_store": True,
    "drift_detection": True,
    "query_rewriting": True,
    "evidence_policy": True,
    "answer_composer": True,
    "e2e_benchmark": True,
}


def run_p1_maturity(report_path: str = "runtime/reports/p1_maturity_gate.json") -> dict:
    gate = P1MaturityGate()
    result = gate.evaluate(DEFAULT_CAPABILITIES)
    gate.write_report(result, report_path)
    return {
        "status": result.status,
        "report": str(Path(report_path)),
        "checks": result.checks,
    }


def main() -> int:
    result = run_p1_maturity()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
