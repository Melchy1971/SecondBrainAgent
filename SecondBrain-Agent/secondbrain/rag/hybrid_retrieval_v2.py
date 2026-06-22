"""P1 v19.4 - Hybrid Retrieval v2.

Combines keyword and vector retrieval via Reciprocal Rank Fusion.
The retriever accepts simple backend protocols so it can run with local,
SQLite, pgvector or mock adapters.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from secondbrain.rag.rrf import RankedItem, FusedItem, reciprocal_rank_fusion


class KeywordBackend(Protocol):
    def search(self, query: str, limit: int) -> list[RankedItem]:
        ...


class VectorBackend(Protocol):
    def search(self, query: str, limit: int) -> list[RankedItem]:
        ...


@dataclass(frozen=True)
class HybridRetrievalResult:
    query: str
    results: list[FusedItem]
    keyword_count: int
    vector_count: int


class HybridRetrievalV2:
    def __init__(self, keyword_backend: KeywordBackend, vector_backend: VectorBackend, *, rrf_k: int = 60) -> None:
        self.keyword_backend = keyword_backend
        self.vector_backend = vector_backend
        self.rrf_k = rrf_k

    def search(self, query: str, *, limit: int = 10, candidate_limit: int = 50) -> HybridRetrievalResult:
        if not query or not query.strip():
            return HybridRetrievalResult(query=query, results=[], keyword_count=0, vector_count=0)
        if limit < 1:
            raise ValueError("limit must be >= 1")
        if candidate_limit < limit:
            candidate_limit = limit

        keyword_items = self.keyword_backend.search(query, candidate_limit)
        vector_items = self.vector_backend.search(query, candidate_limit)

        fused = reciprocal_rank_fusion(
            {"keyword": keyword_items, "vector": vector_items},
            k=self.rrf_k,
            limit=limit,
        )
        return HybridRetrievalResult(
            query=query,
            results=fused,
            keyword_count=len(keyword_items),
            vector_count=len(vector_items),
        )
