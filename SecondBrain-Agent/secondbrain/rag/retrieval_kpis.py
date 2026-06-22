"""P1 v19.3 - retrieval KPI implementations."""

from __future__ import annotations

from math import log2


def recall_at_k(expected_ids: set[str], ranked_ids: list[str], k: int) -> float:
    if not expected_ids:
        return 1.0
    if k < 1:
        return 0.0
    hits = expected_ids.intersection(ranked_ids[:k])
    return len(hits) / len(expected_ids)


def reciprocal_rank(expected_ids: set[str], ranked_ids: list[str]) -> float:
    if not expected_ids:
        return 1.0
    for idx, doc_id in enumerate(ranked_ids, start=1):
        if doc_id in expected_ids:
            return 1.0 / idx
    return 0.0


def ndcg_at_k(expected_ids: set[str], ranked_ids: list[str], k: int) -> float:
    if not expected_ids:
        return 1.0
    dcg = 0.0
    for idx, doc_id in enumerate(ranked_ids[:k], start=1):
        if doc_id in expected_ids:
            dcg += 1.0 / log2(idx + 1)
    ideal_hits = min(len(expected_ids), k)
    idcg = sum(1.0 / log2(idx + 1) for idx in range(1, ideal_hits + 1))
    return 0.0 if idcg == 0 else dcg / idcg


def evaluate_retrieval(expected_ids: set[str], ranked_ids: list[str], k: int = 10) -> dict[str, float]:
    return {
        f"recall_at_{k}": recall_at_k(expected_ids, ranked_ids, k),
        "mrr": reciprocal_rank(expected_ids, ranked_ids),
        f"ndcg_at_{k}": ndcg_at_k(expected_ids, ranked_ids, k),
    }
