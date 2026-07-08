"""P0.2 - vector search application service."""

from __future__ import annotations

from typing import Any

from secondbrain.rag.hybrid_score import HybridScoreCalculator


class VectorSearchService:
    def __init__(self, repository: Any, score_calculator: HybridScoreCalculator | None = None):
        if repository is None or not hasattr(repository, "search"):
            raise TypeError("repository must provide a search(query_embedding, limit=...) method")
        self.repository = repository
        self.score_calculator = score_calculator or HybridScoreCalculator()

    def search(self, query_embedding: list[float], *, limit: int = 10) -> list[dict]:
        if limit <= 0:
            return []
        results = self.repository.search(query_embedding, limit=limit)
        normalized: list[dict] = []
        for result in results:
            metadata = dict(getattr(result, "metadata", {}) or {})
            semantic_score = float(getattr(result, "score", 0.0) or 0.0)
            bm25_score = float(metadata.get("bm25_score", metadata.get("bm25", 0.0)) or 0.0)
            recency_score = float(metadata.get("recency_score", metadata.get("recency", 0.0)) or 0.0)
            importance_score = float(metadata.get("importance_score", metadata.get("importance", 0.0)) or 0.0)
            has_auxiliary_scores = any(
                key in metadata
                for key in (
                    "bm25_score", "bm25",
                    "recency_score", "recency",
                    "importance_score", "importance",
                )
            )
            hybrid_score = (
                semantic_score
                if not has_auxiliary_scores
                else self.score_calculator.score(
                    semantic_score=semantic_score,
                    bm25_score=bm25_score,
                    recency_score=recency_score,
                    importance_score=importance_score,
                )
            )
            normalized.append(
                {
                    "id": getattr(result, "id", None),
                    "owner_type": getattr(result, "owner_type", None),
                    "owner_id": getattr(result, "owner_id", None),
                    "distance": getattr(result, "distance", None),
                    "semantic_score": semantic_score,
                    "bm25_score": bm25_score,
                    "recency_score": recency_score,
                    "importance_score": importance_score,
                    "hybrid_score": hybrid_score,
                    "metadata": metadata,
                }
            )
        return sorted(normalized, key=lambda item: item["hybrid_score"], reverse=True)
