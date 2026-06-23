"""RAG reranking layer with deterministic fallback behavior.

P1.1.4 adds a small production-safe reranker abstraction.  It accepts the
canonical SearchResult objects produced by hybrid retrieval, can delegate to an
external scorer, and never blocks retrieval when the scorer is unavailable.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Protocol

from secondbrain.rag.retrieval.score_fusion import SearchResult


class RerankScorer(Protocol):
    """Scores query/result pairs for second-stage ranking."""

    def score(self, query: str, result: SearchResult) -> float:
        ...


@dataclass(frozen=True)
class RerankerConfig:
    """Configuration for second-stage retrieval reranking."""

    candidate_limit: int = 50
    result_limit: int = 10
    enabled: bool = True
    fail_open: bool = True

    def __post_init__(self) -> None:
        if self.candidate_limit < 1:
            raise ValueError("candidate_limit must be >= 1")
        if self.result_limit < 1:
            raise ValueError("result_limit must be >= 1")


class KeywordOverlapScorer:
    """Local deterministic scorer used as default and offline fallback.

    It is intentionally simple: score = ratio of query terms found in the
    candidate text. Existing hybrid score is not discarded; Reranker combines
    both values to keep upstream retrieval signal stable.
    """

    def score(self, query: str, result: SearchResult) -> float:
        query_terms = _terms(query)
        if not query_terms:
            return 0.0
        text_terms = _terms(result.text)
        if not text_terms:
            return 0.0
        return len(query_terms.intersection(text_terms)) / len(query_terms)


class Reranker:
    """Second-stage reranker with fail-open semantics."""

    def __init__(self, scorer: RerankScorer | None = None, config: RerankerConfig | None = None) -> None:
        self.scorer = scorer or KeywordOverlapScorer()
        self.config = config or RerankerConfig()

    def rerank(self, query: str, results: Iterable[SearchResult], limit: int | None = None) -> list[SearchResult]:
        materialized = list(results)
        effective_limit = limit or self.config.result_limit
        if effective_limit <= 0 or not materialized:
            return []

        baseline = sorted(materialized, key=_stable_retrieval_order)
        candidates = baseline[: self.config.candidate_limit]
        if not self.config.enabled or not query.strip():
            return baseline[:effective_limit]

        try:
            reranked = [self._with_rerank_score(query, result) for result in candidates]
        except Exception:
            if self.config.fail_open:
                return baseline[:effective_limit]
            raise

        return sorted(reranked, key=_stable_rerank_order)[:effective_limit]

    def _with_rerank_score(self, query: str, result: SearchResult) -> SearchResult:
        rerank_score = float(self.scorer.score(query, result))
        hybrid_score = float(result.score)
        final_score = (0.7 * rerank_score) + (0.3 * hybrid_score)
        metadata = dict(result.metadata)
        metadata.update(
            {
                "rerank_score": rerank_score,
                "pre_rerank_score": hybrid_score,
                "reranker": self.scorer.__class__.__name__,
            }
        )
        return SearchResult(
            document_id=result.document_id,
            chunk_id=result.chunk_id,
            text=result.text,
            score=final_score,
            metadata=metadata,
        )


def _terms(text: str) -> set[str]:
    return {token for token in "".join(ch.lower() if ch.isalnum() else " " for ch in text).split() if token}


def _stable_retrieval_order(result: SearchResult) -> tuple[float, str, str]:
    return (-float(result.score), result.document_id, result.chunk_id)


def _stable_rerank_order(result: SearchResult) -> tuple[float, str, str]:
    return (-float(result.score), result.document_id, result.chunk_id)
