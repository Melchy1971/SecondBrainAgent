from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from .search_query import SearchQuery


@dataclass
class SearchHistory:
    max_entries: int = 50
    entries: list[dict] = field(default_factory=list)

    def add(self, query: SearchQuery, result_count: int) -> None:
        entry = {
            "query": query.normalized().cache_key(),
            "text": query.normalized().text,
            "workspace_id": query.normalized().workspace_id,
            "result_count": int(result_count),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.entries.insert(0, entry)
        self.entries = self.entries[: self.max_entries]

    def recent_texts(self) -> list[str]:
        seen: set[str] = set()
        values: list[str] = []
        for entry in self.entries:
            text = entry.get("text", "")
            if text and text not in seen:
                seen.add(text)
                values.append(text)
        return values
