from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SearchQuery:
    text: str
    workspace_id: str | None = None
    tags: list[str] = field(default_factory=list)
    status: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    limit: int = 25
    offset: int = 0

    def normalized(self) -> "SearchQuery":
        limit = max(1, min(int(self.limit), 100))
        offset = max(0, int(self.offset))
        return SearchQuery(
            text=" ".join((self.text or "").strip().split()),
            workspace_id=(self.workspace_id or None),
            tags=sorted({t.strip() for t in self.tags if t and t.strip()}),
            status=sorted({s.strip().upper() for s in self.status if s and s.strip()}),
            sources=sorted({s.strip() for s in self.sources if s and s.strip()}),
            limit=limit,
            offset=offset,
        )

    def cache_key(self) -> str:
        q = self.normalized()
        return "|".join([
            q.text.lower(),
            q.workspace_id or "*",
            ",".join(q.tags),
            ",".join(q.status),
            ",".join(q.sources),
            str(q.limit),
            str(q.offset),
        ])
