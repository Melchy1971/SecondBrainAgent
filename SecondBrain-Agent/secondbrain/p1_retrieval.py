from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class RetrievalThresholds:
    min_hit_rate: float = 0.75
    min_recall_at_k: float = 0.75
    min_mrr: float = 0.50
    min_ndcg: float = 0.55
    min_confidence: float = 0.15


def reciprocal_rank_fusion(
    ranked_lists: Iterable[list[dict[str, Any]]],
    *,
    id_key: str = "chunk_id",
    rank_constant: int = 60,
    weights: list[float] | None = None,
) -> list[dict[str, Any]]:
    """Merge ranked retrieval results with deterministic Reciprocal Rank Fusion.

    The function is intentionally dependency-free and stable under ties. Each hit keeps
    its original payload while gaining `rrf_score`, `rank_sources`, and per-source ranks.
    """
    merged: dict[str, dict[str, Any]] = {}
    lists = list(ranked_lists)
    weights = weights or [1.0] * len(lists)
    for source_index, hits in enumerate(lists):
        weight = weights[source_index] if source_index < len(weights) else 1.0
        source_name = hits[0].get("retrieval_source", f"source_{source_index}") if hits else f"source_{source_index}"
        for rank, hit in enumerate(hits, 1):
            hit_id = str(hit.get(id_key) or "")
            if not hit_id:
                continue
            current = merged.setdefault(hit_id, dict(hit))
            current.setdefault("rank_sources", [])
            if source_name not in current["rank_sources"]:
                current["rank_sources"].append(source_name)
            current.setdefault("source_ranks", {})[source_name] = rank
            current["rrf_score"] = float(current.get("rrf_score", 0.0)) + weight / (rank_constant + rank)
            current.setdefault("raw_scores", {})[source_name] = hit.get("score", 0.0)
    return sorted(merged.values(), key=lambda h: (-float(h.get("rrf_score", 0.0)), h.get("title", ""), h.get(id_key, "")))


def _dcg(relevances: list[float]) -> float:
    return sum(rel / math.log2(idx + 2) for idx, rel in enumerate(relevances))


def evaluate_ranked_hits(hits: list[dict[str, Any]], expected_terms: list[str], *, k: int = 10) -> dict[str, Any]:
    """Compute offline retrieval KPIs without labeled datasets.

    Relevance is estimated by expected-term coverage in hit text/title/source. This is
    not a substitute for a golden eval set, but it gives a deterministic regression gate
    until curated labels exist.
    """
    normalized_terms = [t.lower() for t in expected_terms if t.strip()]
    selected = hits[: max(1, int(k))]
    if not normalized_terms:
        return {"recall_at_k": 0.0, "mrr": 0.0, "ndcg": 0.0, "relevant_hits": 0, "expected_terms": []}
    relevances: list[float] = []
    first_relevant_rank = 0
    covered_terms: set[str] = set()
    for rank, hit in enumerate(selected, 1):
        haystack = " ".join(str(hit.get(key, "")) for key in ("text", "snippet", "title", "source")).lower()
        matched = {term for term in normalized_terms if term in haystack}
        covered_terms.update(matched)
        relevance = len(matched) / len(normalized_terms)
        relevances.append(relevance)
        if matched and first_relevant_rank == 0:
            first_relevant_rank = rank
    ideal_relevances = sorted(relevances, reverse=True)
    ideal = _dcg(ideal_relevances)
    ndcg = _dcg(relevances) / ideal if ideal > 0 else 0.0
    return {
        "recall_at_k": round(len(covered_terms) / len(normalized_terms), 4),
        "mrr": round(1.0 / first_relevant_rank, 4) if first_relevant_rank else 0.0,
        "ndcg": round(ndcg, 4),
        "relevant_hits": sum(1 for value in relevances if value > 0),
        "expected_terms": normalized_terms,
        "covered_terms": sorted(covered_terms),
    }


def production_decision(metrics: dict[str, Any], thresholds: RetrievalThresholds | None = None) -> dict[str, Any]:
    thresholds = thresholds or RetrievalThresholds()
    checks = [
        {"name": "hit_rate", "ok": float(metrics.get("hit_rate", 0.0)) >= thresholds.min_hit_rate, "threshold": thresholds.min_hit_rate, "actual": float(metrics.get("hit_rate", 0.0))},
        {"name": "recall_at_k", "ok": float(metrics.get("avg_recall_at_k", 0.0)) >= thresholds.min_recall_at_k, "threshold": thresholds.min_recall_at_k, "actual": float(metrics.get("avg_recall_at_k", 0.0))},
        {"name": "mrr", "ok": float(metrics.get("avg_mrr", 0.0)) >= thresholds.min_mrr, "threshold": thresholds.min_mrr, "actual": float(metrics.get("avg_mrr", 0.0))},
        {"name": "ndcg", "ok": float(metrics.get("avg_ndcg", 0.0)) >= thresholds.min_ndcg, "threshold": thresholds.min_ndcg, "actual": float(metrics.get("avg_ndcg", 0.0))},
        {"name": "confidence", "ok": float(metrics.get("avg_confidence", 0.0)) >= thresholds.min_confidence, "threshold": thresholds.min_confidence, "actual": float(metrics.get("avg_confidence", 0.0))},
    ]
    blockers = sum(1 for check in checks if not check["ok"])
    return {"ok": blockers == 0, "status": "pass" if blockers == 0 else "blocked", "blockers": blockers, "checks": checks}
