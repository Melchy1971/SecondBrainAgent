"""P3 v20.2 - Memory Summarization Pipeline."""

class MemorySummarizer:
    def summarize(self, texts: list[str], max_items: int = 5) -> str:
        texts = [t.strip() for t in texts if t and t.strip()]
        return " | ".join(texts[:max_items])
