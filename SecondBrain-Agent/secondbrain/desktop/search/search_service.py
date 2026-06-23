from __future__ import annotations

from typing import Protocol
from .search_query import SearchQuery
from .search_result import SearchResult
from .search_filters import SearchFilters
from .search_facets import SearchFacets
from .search_history import SearchHistory
from .search_state import SearchState
from .search_events import (
    SEARCH_COMPLETED,
    SEARCH_FAILED,
    SEARCH_HISTORY_UPDATED,
    SEARCH_STARTED,
    SearchEventBus,
)


class SearchBackend(Protocol):
    def search(self, query: SearchQuery) -> list[SearchResult]:
        ...


class InMemorySearchBackend:
    def __init__(self, documents: list[SearchResult] | None = None) -> None:
        self.documents = documents or []

    def search(self, query: SearchQuery) -> list[SearchResult]:
        q = query.normalized()
        words = [w.lower() for w in q.text.split() if w]
        scored: list[SearchResult] = []
        filters = SearchFilters(workspace_id=q.workspace_id, tags=q.tags, status=q.status, sources=q.sources)
        for doc in self.documents:
            if not filters.matches(doc):
                continue
            haystack = f"{doc.title} {doc.snippet} {' '.join(doc.tags)}".lower()
            if words and not all(word in haystack for word in words):
                continue
            score = doc.score + sum(haystack.count(word) for word in words)
            scored.append(SearchResult(
                document_id=doc.document_id,
                title=doc.title,
                snippet=doc.snippet,
                score=score,
                tags=doc.tags,
                source=doc.source,
                workspace_id=doc.workspace_id,
                status=doc.status,
                metadata=doc.metadata,
            ).sanitized())
        scored.sort(key=lambda r: (-r.score, r.title.lower(), r.document_id))
        return scored[q.offset : q.offset + q.limit]


class SearchService:
    def __init__(
        self,
        backend: SearchBackend,
        *,
        history: SearchHistory | None = None,
        state: SearchState | None = None,
        events: SearchEventBus | None = None,
    ) -> None:
        self.backend = backend
        self.history = history or SearchHistory()
        self.state = state or SearchState()
        self.events = events or SearchEventBus()

    def search(self, query: SearchQuery) -> tuple[list[SearchResult], SearchFacets]:
        q = query.normalized()
        self.state.start(q)
        self.events.emit(SEARCH_STARTED, query=q.cache_key())
        try:
            results = [r.sanitized() for r in self.backend.search(q)]
            facets = SearchFacets.from_results(results)
            self.history.add(q, len(results))
            self.state.complete(results, facets)
            self.events.emit(SEARCH_COMPLETED, count=len(results))
            self.events.emit(SEARCH_HISTORY_UPDATED, count=len(self.history.entries))
            return results, facets
        except Exception as exc:
            self.state.fail(exc)
            self.events.emit(SEARCH_FAILED, error=str(exc))
            raise
