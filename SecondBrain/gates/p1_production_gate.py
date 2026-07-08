"""P1 v19.4 - P1 Production Gate.

Evaluates RAG production readiness from measurable retrieval metrics.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import json


@dataclass(frozen=True)
class P1GateThresholds:
    min_recall_at_10: float = 0.80
    min_mrr: float = 0.70
    min_ndcg_at_10: float = 0.75
    min_queries: int = 1


@dataclass(frozen=True)
class P1GateResult:
    status: str
    checks: dict[str, dict]
    summary: dict[str, float | int]


class P1ProductionGate:
    def __init__(self, thresholds: P1GateThresholds | None = None) -> None:
        self.thresholds = thresholds or P1GateThresholds()

    def evaluate(self, summary: dict[str, float | int]) -> P1GateResult:
        checks = {
            "query_volume": self._check(float(summary.get("records", 0)), float(self.thresholds.min_queries), ">="),
            "recall_at_10": self._check(float(summary.get("avg_recall_at_10", 0.0)), self.thresholds.min_recall_at_10, ">="),
            "mrr": self._check(float(summary.get("avg_mrr", 0.0)), self.thresholds.min_mrr, ">="),
            "ndcg_at_10": self._check(float(summary.get("avg_ndcg_at_10", 0.0)), self.thresholds.min_ndcg_at_10, ">="),
        }
        status = "PASS" if all(check["status"] == "PASS" for check in checks.values()) else "FAIL"
        return P1GateResult(status=status, checks=checks, summary=summary)

    @staticmethod
    def _check(actual: float, expected: float, operator: str) -> dict:
        passed = actual >= expected
        return {
            "status": "PASS" if passed else "FAIL",
            "actual": actual,
            "expected": expected,
            "operator": operator,
        }

    def write_report(self, result: P1GateResult, path: str | Path = "runtime/reports/p1_production_gate.json") -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(asdict(result), indent=2, sort_keys=True), encoding="utf-8")
        return target
