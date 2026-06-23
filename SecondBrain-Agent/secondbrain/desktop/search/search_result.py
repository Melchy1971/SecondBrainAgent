from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SearchResult:
    document_id: str
    title: str
    snippet: str
    score: float
    tags: list[str] = field(default_factory=list)
    source: str = "unknown"
    workspace_id: str = "default"
    status: str = "INDEXED"
    metadata: dict = field(default_factory=dict)

    def sanitized(self, *, max_snippet_chars: int = 320) -> "SearchResult":
        snippet = " ".join((self.snippet or "").split())
        if len(snippet) > max_snippet_chars:
            snippet = snippet[: max(0, max_snippet_chars - 1)].rstrip() + "…"
        metadata = {
            k: v
            for k, v in (self.metadata or {}).items()
            if k not in {"ownerUserId", "workspaceId", "documentId", "internal_id"}
        }
        return SearchResult(
            document_id=self.document_id,
            title=self.title or "Untitled",
            snippet=snippet,
            score=float(self.score),
            tags=list(self.tags),
            source=self.source,
            workspace_id=self.workspace_id,
            status=self.status,
            metadata=metadata,
        )
