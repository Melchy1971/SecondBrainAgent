"""P1 v19.5 - end-to-end RAG benchmark suite."""

from __future__ import annotations

from dataclasses import dataclass

from secondbrain.rag.retrieval_kpis import evaluate_retrieval
from secondbrain.rag.kpi_store import RetrievalKpiStore


@dataclass(frozen=True)
class BenchmarkCase:
    query_id: str
    query: str
    expected_ids: set[str]


@dataclass(frozen=True)
class BenchmarkResult:
    cases: int
    averages: dict[str, float]
    per_case: list[dict]


class E2ERagBenchmarkSuite:
    def __init__(self, retriever, store: RetrievalKpiStore | None = None) -> None:
        self.retriever = retriever
        self.store = store

    def run(self, cases: list[BenchmarkCase], *, k: int = 10) -> BenchmarkResult:
        per_case = []
        sums: dict[str, float] = {}

        for case in cases:
            result = self.retriever.search(case.query, limit=k)
            ranked_ids = [item.id for item in result.results]
            metrics = evaluate_retrieval(case.expected_ids, ranked_ids, k=k)
            if self.store is not None:
                self.store.append(case.query_id, case.query, metrics)
            row = {"query_id": case.query_id, "query": case.query, "metrics": metrics, "ranked_ids": ranked_ids}
            per_case.append(row)
            for key, value in metrics.items():
                sums[key] = sums.get(key, 0.0) + value

        count = len(cases)
        averages = {key: value / count for key, value in sums.items()} if count else {}
        return BenchmarkResult(cases=count, averages=averages, per_case=per_case)
