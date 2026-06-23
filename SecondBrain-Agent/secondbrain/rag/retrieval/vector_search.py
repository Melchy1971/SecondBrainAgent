"""Vector-search adapter interfaces and deterministic in-memory implementation."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Protocol

from .score_fusion import SearchResult


class VectorSearch(Protocol):
    def search(self, query_vector: list[float], limit: int = 20) -> list[SearchResult]:
        ...


@dataclass(frozen=True)
class VectorChunk:
    document_id: str
    chunk_id: str
    text: str
    vector: list[float]


class InMemoryVectorSearch:
    """Small deterministic vector adapter for tests and local fallback."""

    def __init__(self, chunks: Iterable[VectorChunk]) -> None:
        self._chunks = list(chunks)

    def search(self, query_vector: list[float], limit: int = 20) -> list[SearchResult]:
        if limit <= 0 or not query_vector:
            return []
        results = [
            SearchResult(
                document_id=chunk.document_id,
                chunk_id=chunk.chunk_id,
                text=chunk.text,
                score=_cosine_similarity(query_vector, chunk.vector),
                metadata={"source": "vector"},
            )
            for chunk in self._chunks
            if chunk.vector
        ]
        return sorted(results, key=lambda r: (-r.score, r.document_id, r.chunk_id))[:limit]


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    size = min(len(left), len(right))
    if size == 0:
        return 0.0
    dot = sum(left[i] * right[i] for i in range(size))
    left_norm = math.sqrt(sum(left[i] * left[i] for i in range(size)))
    right_norm = math.sqrt(sum(right[i] * right[i] for i in range(size)))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)
