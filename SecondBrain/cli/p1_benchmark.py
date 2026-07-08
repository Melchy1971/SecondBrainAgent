"""P1 v19.6 - minimal benchmark CLI adapter.

This adapter is intentionally deterministic and dependency-light. It validates
that benchmark execution, KPI calculation and report serialization work before
external vector stores or LLM providers are required.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from secondbrain.rag.e2e_benchmark_suite import E2ERagBenchmarkSuite, BenchmarkCase
from secondbrain.rag.rrf import RankedItem


class StaticBenchmarkRetriever:
    def search(self, query: str, limit: int = 10):
        class Result:
            results = [RankedItem("doc1"), RankedItem("doc2"), RankedItem("doc3")]
        return Result()


def run_p1_benchmark(report_path: str = "runtime/reports/p1_benchmark.json") -> dict:
    suite = E2ERagBenchmarkSuite(StaticBenchmarkRetriever())
    result = suite.run([
        BenchmarkCase("baseline-1", "baseline retrieval", {"doc1"}),
        BenchmarkCase("baseline-2", "secondary retrieval", {"doc2"}),
    ], k=3)

    payload = {
        "status": "PASS" if result.cases > 0 else "FAIL",
        "cases": result.cases,
        "averages": result.averages,
        "per_case": result.per_case,
    }
    target = Path(report_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload


def main() -> int:
    result = run_p1_benchmark()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
