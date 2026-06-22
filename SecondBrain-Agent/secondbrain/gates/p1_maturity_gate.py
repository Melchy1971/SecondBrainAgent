"""P1 v19.5 - maturity gate.

Closes P1 when retrieval, evidence, benchmark and answer grounding are present.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import json


@dataclass(frozen=True)
class P1MaturityResult:
    status: str
    checks: dict[str, dict]


class P1MaturityGate:
    required_capabilities = [
        "hybrid_retrieval",
        "rrf",
        "retrieval_kpis",
        "kpi_store",
        "drift_detection",
        "query_rewriting",
        "evidence_policy",
        "answer_composer",
        "e2e_benchmark",
    ]

    def evaluate(self, capabilities: dict[str, bool]) -> P1MaturityResult:
        checks = {
            name: {"status": "PASS" if capabilities.get(name, False) else "FAIL"}
            for name in self.required_capabilities
        }
        status = "PASS" if all(c["status"] == "PASS" for c in checks.values()) else "FAIL"
        return P1MaturityResult(status=status, checks=checks)

    def write_report(self, result: P1MaturityResult, path: str | Path = "runtime/reports/p1_maturity_gate.json") -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(asdict(result), indent=2, sort_keys=True), encoding="utf-8")
        return target
