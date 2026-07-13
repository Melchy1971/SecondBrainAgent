"""P3 v20.3 - Memory Deduplication."""

class MemoryDeduplicator:
    def deduplicate(self, texts: list[str]) -> list[str]:
        seen = set()
        result = []
        for text in texts:
            key = " ".join((text or "").strip().lower().split())
            if key and key not in seen:
                seen.add(key)
                result.append(text)
        return result
