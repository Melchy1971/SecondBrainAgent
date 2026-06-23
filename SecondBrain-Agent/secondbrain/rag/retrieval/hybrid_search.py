"""Hybrid vector + BM25 retrieval orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .bm25_search import BM25Search
from .score_fusion import SearchResult, WeightedScoreFusion
from .vector_search import VectorSearch


class QueryEmbedder(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]:
        ...


@dataclass(frozen=True)
class HybridSearchConfig:
    vector_weight: float = 0.65
    bm25_weight: float = 0.35
    candidate_limit: int = 50


class HybridSearch:
    """Run lexical and vector search and merge their candidates."""

    def __init__(
        self,
        vector_search: VectorSearch,
        bm25_search: BM25Search,
        embedder: QueryEmbedder,
        config: HybridSearchConfig | None = None,
    ) -> None:
        self._vector_search = vector_search
        self._bm25_search = bm25_search
        self._embedder = embedder
        self._config = config or HybridSearchConfig()
        self._fusion = WeightedScoreFusion(
            vector_weight=self._config.vector_weight,
            bm25_weight=self._config.bm25_weight,
        )

    def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        normalized_query = (query or "").strip()
        if limit <= 0 or not normalized_query:
            return []

        embeddings = self._embedder.embed([normalized_query])
        query_vector = embeddings[0] if embeddings else []
        vector_results = self._vector_search.search(query_vector, limit=self._config.candidate_limit)
        bm25_results = self._bm25_search.search(normalized_query, limit=self._config.candidate_limit)
        return self._fusion.fuse(vector_results, bm25_results, limit=limit)
