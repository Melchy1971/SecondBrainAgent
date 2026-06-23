from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, Any

from .search_query import SearchQuery
from .search_result import SearchResult


@dataclass(frozen=True)
class HybridSearchSettings:
    vector_weight: float = 0.65
    bm25_weight: float = 0.35
    limit_multiplier: int = 3
    expose_score_breakdown: bool = True

    def normalized(self) -> "HybridSearchSettings":
        vector = max(0.0, float(self.vector_weight))
        bm25 = max(0.0, float(self.bm25_weight))
        total = vector + bm25
        if total <= 0:
            vector, bm25, total = 0.65, 0.35, 1.0
        return HybridSearchSettings(
            vector_weight=round(vector / total, 6),
            bm25_weight=round(bm25 / total, 6),
            limit_multiplier=max(1, min(int(self.limit_multiplier), 10)),
            expose_score_breakdown=bool(self.expose_score_breakdown),
        )


@dataclass(frozen=True)
class HybridScoreBreakdown:
    vector_score: float = 0.0
    bm25_score: float = 0.0
    hybrid_score: float = 0.0
    source: str = "hybrid"

    def as_metadata(self) -> dict[str, Any]:
        return {
            "score_source": self.source,
            "vector_score": round(float(self.vector_score), 6),
            "bm25_score": round(float(self.bm25_score), 6),
            "hybrid_score": round(float(self.hybrid_score), 6),
        }


@dataclass(frozen=True)
class HybridCandidate:
    document_id: str
    title: str
    snippet: str
    vector_score: float = 0.0
    bm25_score: float = 0.0
    tags: list[str] = field(default_factory=list)
    source: str = "unknown"
    workspace_id: str = "default"
    status: str = "INDEXED"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_search_result(self, settings: HybridSearchSettings) -> SearchResult:
        normalized = settings.normalized()
        hybrid_score = (normalized.vector_weight * float(self.vector_score)) + (normalized.bm25_weight * float(self.bm25_score))
        metadata = dict(self.metadata or {})
        if normalized.expose_score_breakdown:
            metadata.update(HybridScoreBreakdown(
                vector_score=self.vector_score,
                bm25_score=self.bm25_score,
                hybrid_score=hybrid_score,
            ).as_metadata())
        return SearchResult(
            document_id=self.document_id,
            title=self.title,
            snippet=self.snippet,
            score=hybrid_score,
            tags=list(self.tags),
            source=self.source,
            workspace_id=self.workspace_id,
            status=self.status,
            metadata=metadata,
        ).sanitized()


class HybridSearchEngine(Protocol):
    def search(self, query: SearchQuery, *, limit: int) -> list[HybridCandidate | SearchResult | dict[str, Any]]:
        ...


class HybridSearchBackendAdapter:
    """Desktop SearchBackend adapter for RAG hybrid retrieval engines."""

    def __init__(self, engine: HybridSearchEngine, settings: HybridSearchSettings | None = None) -> None:
        self.engine = engine
        self.settings = (settings or HybridSearchSettings()).normalized()

    def search(self, query: SearchQuery) -> list[SearchResult]:
        q = query.normalized()
        candidate_limit = min(500, q.limit * self.settings.limit_multiplier + q.offset)
        raw_candidates = self.engine.search(q, limit=candidate_limit)
        results = [self._coerce_candidate(candidate).to_search_result(self.settings) for candidate in raw_candidates]
        results.sort(key=lambda result: (-result.score, result.title.lower(), result.document_id))
        return results[q.offset : q.offset + q.limit]

    def _coerce_candidate(self, candidate: HybridCandidate | SearchResult | dict[str, Any]) -> HybridCandidate:
        if isinstance(candidate, HybridCandidate):
            return candidate
        if isinstance(candidate, SearchResult):
            vector = float(candidate.metadata.get("vector_score", candidate.score) if candidate.metadata else candidate.score)
            bm25 = float(candidate.metadata.get("bm25_score", 0.0) if candidate.metadata else 0.0)
            return HybridCandidate(
                document_id=candidate.document_id,
                title=candidate.title,
                snippet=candidate.snippet,
                vector_score=vector,
                bm25_score=bm25,
                tags=list(candidate.tags),
                source=candidate.source,
                workspace_id=candidate.workspace_id,
                status=candidate.status,
                metadata=dict(candidate.metadata or {}),
            )
        return HybridCandidate(
            document_id=str(candidate.get("document_id") or candidate.get("id") or ""),
            title=str(candidate.get("title") or "Untitled"),
            snippet=str(candidate.get("snippet") or candidate.get("text") or ""),
            vector_score=float(candidate.get("vector_score", 0.0)),
            bm25_score=float(candidate.get("bm25_score", 0.0)),
            tags=list(candidate.get("tags") or []),
            source=str(candidate.get("source") or "unknown"),
            workspace_id=str(candidate.get("workspace_id") or "default"),
            status=str(candidate.get("status") or "INDEXED"),
            metadata=dict(candidate.get("metadata") or {}),
        )
