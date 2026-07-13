from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from .search_result import SearchResult


@dataclass(frozen=True)
class SearchFilters:
    workspace_id: str | None = None
    tags: list[str] = field(default_factory=list)
    status: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    created_after: datetime | None = None
    created_before: datetime | None = None

    def matches(self, result: SearchResult) -> bool:
        if self.workspace_id and result.workspace_id != self.workspace_id:
            return False
        if self.tags and not set(self.tags).issubset(set(result.tags)):
            return False
        if self.status and result.status.upper() not in {s.upper() for s in self.status}:
            return False
        if self.sources and result.source not in set(self.sources):
            return False
        created_at = result.metadata.get("created_at") if result.metadata else None
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at)
            except ValueError:
                created_at = None
        if self.created_after and created_at and created_at < self.created_after:
            return False
        if self.created_before and created_at and created_at > self.created_before:
            return False
        return True
