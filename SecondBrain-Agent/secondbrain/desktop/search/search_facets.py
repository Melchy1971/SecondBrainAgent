from __future__ import annotations

from dataclasses import dataclass
from collections import Counter
from .search_result import SearchResult


@dataclass(frozen=True)
class FacetBucket:
    value: str
    count: int


@dataclass(frozen=True)
class SearchFacets:
    workspaces: list[FacetBucket]
    tags: list[FacetBucket]
    status: list[FacetBucket]
    sources: list[FacetBucket]

    @staticmethod
    def from_results(results: list[SearchResult]) -> "SearchFacets":
        workspace_counter = Counter(r.workspace_id for r in results)
        tag_counter = Counter(tag for r in results for tag in r.tags)
        status_counter = Counter(r.status for r in results)
        source_counter = Counter(r.source for r in results)

        def buckets(counter: Counter) -> list[FacetBucket]:
            return [FacetBucket(value=str(k), count=v) for k, v in sorted(counter.items(), key=lambda item: (-item[1], str(item[0])))]

        return SearchFacets(
            workspaces=buckets(workspace_counter),
            tags=buckets(tag_counter),
            status=buckets(status_counter),
            sources=buckets(source_counter),
        )
