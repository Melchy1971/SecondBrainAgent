"""P3 v20.2 - Semantic Search over Memory."""

class SemanticMemorySearch:
    def search(self, query: str, items: list, limit: int = 10):
        query = query.lower()
        matches = [
            item for item in items
            if query in getattr(item, "text", "").lower()
        ]
        return matches[:limit]
