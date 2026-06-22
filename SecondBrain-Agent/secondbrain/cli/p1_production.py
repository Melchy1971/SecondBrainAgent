"""P1 v19.4 - CLI adapter for P1 production gate."""

from __future__ import annotations

import json
from pathlib import Path

from secondbrain.gates.p1_production_gate import P1ProductionGate
from secondbrain.rag.kpi_store import RetrievalKpiStore


def run_p1_production_gate(kpi_path: str = "runtime/rag/retrieval_kpis.jsonl", report_path: str = "runtime/reports/p1_production_gate.json") -> dict:
    store = RetrievalKpiStore(kpi_path)
    gate = P1ProductionGate()
    result = gate.evaluate(store.summary())
    gate.write_report(result, report_path)
    return {
        "status": result.status,
        "report": str(Path(report_path)),
        "summary": result.summary,
        "checks": result.checks,
    }


def main() -> int:
    result = run_p1_production_gate()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
