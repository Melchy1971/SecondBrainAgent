"""P3 v20.2 - Memory Importance Scoring."""

class MemoryImportanceScorer:
    def score(self, text: str, access_count: int = 0, tags: list[str] | None = None) -> float:
        tags = tags or []
        length_factor = min(len((text or "").split()) / 100.0, 1.0)
        tag_factor = min(len(tags) * 0.1, 0.5)
        access_factor = min(access_count * 0.05, 1.0)
        return round(length_factor + tag_factor + access_factor, 3)
