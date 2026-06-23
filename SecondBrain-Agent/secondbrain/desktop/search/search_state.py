from __future__ import annotations

from dataclasses import dataclass, field
from .search_query import SearchQuery
from .search_result import SearchResult
from .search_facets import SearchFacets


@dataclass
class SearchState:
    last_query: SearchQuery | None = None
    results: list[SearchResult] = field(default_factory=list)
    facets: SearchFacets | None = None
    loading: bool = False
    error: str | None = None

    def start(self, query: SearchQuery) -> None:
        self.last_query = query.normalized()
        self.loading = True
        self.error = None

    def complete(self, results: list[SearchResult], facets: SearchFacets) -> None:
        self.results = results
        self.facets = facets
        self.loading = False
        self.error = None

    def fail(self, error: Exception | str) -> None:
        self.loading = False
        self.error = str(error)
