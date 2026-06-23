"""Score normalization and fusion for hybrid retrieval."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class SearchResult:
    """Canonical retrieval result used by vector, lexical and hybrid search."""

    document_id: str
    chunk_id: str
    text: str
    score: float
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @property
    def key(self) -> tuple[str, str]:
        return (self.document_id, self.chunk_id)


def normalize_scores(results: Iterable[SearchResult]) -> dict[tuple[str, str], float]:
    """Normalize arbitrary positive/negative scores to a deterministic 0..1 range."""

    materialized = list(results)
    if not materialized:
        return {}
    scores = [float(r.score) for r in materialized]
    minimum = min(scores)
    maximum = max(scores)
    if maximum == minimum:
        return {r.key: 1.0 for r in materialized}
    span = maximum - minimum
    return {r.key: (float(r.score) - minimum) / span for r in materialized}


class WeightedScoreFusion:
    """Combine vector and BM25 scores with configurable weights."""

    def __init__(self, vector_weight: float = 0.65, bm25_weight: float = 0.35) -> None:
        if vector_weight < 0 or bm25_weight < 0:
            raise ValueError("fusion weights must be >= 0")
        if vector_weight == 0 and bm25_weight == 0:
            raise ValueError("at least one fusion weight must be > 0")
        total = vector_weight + bm25_weight
        self.vector_weight = vector_weight / total
        self.bm25_weight = bm25_weight / total

    def fuse(
        self,
        vector_results: Iterable[SearchResult],
        bm25_results: Iterable[SearchResult],
        limit: int = 10,
    ) -> list[SearchResult]:
        if limit <= 0:
            return []

        vector_list = list(vector_results)
        bm25_list = list(bm25_results)
        vector_scores = normalize_scores(vector_list)
        bm25_scores = normalize_scores(bm25_list)

        by_key: dict[tuple[str, str], SearchResult] = {}
        for result in [*vector_list, *bm25_list]:
            current = by_key.get(result.key)
            if current is None or result.score > current.score:
                by_key[result.key] = result

        fused: list[SearchResult] = []
        for key, result in by_key.items():
            score = (
                self.vector_weight * vector_scores.get(key, 0.0)
                + self.bm25_weight * bm25_scores.get(key, 0.0)
            )
            metadata = dict(result.metadata)
            metadata.update(
                {
                    "vector_score": vector_scores.get(key, 0.0),
                    "bm25_score": bm25_scores.get(key, 0.0),
                    "fusion": "weighted_sum",
                }
            )
            fused.append(
                SearchResult(
                    document_id=result.document_id,
                    chunk_id=result.chunk_id,
                    text=result.text,
                    score=score,
                    metadata=metadata,
                )
            )

        return sorted(
            fused,
            key=lambda r: (-r.score, r.document_id, r.chunk_id),
        )[:limit]
