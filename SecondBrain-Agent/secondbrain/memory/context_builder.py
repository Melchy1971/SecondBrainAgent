"""P3 v20.1 - Context Builder."""

from secondbrain.memory.memory_ranker import MemoryRanker


class ContextBuilder:
    def __init__(self):
        self.ranker = MemoryRanker()

    def build(self, memories, limit: int = 10):
        ranked = self.ranker.rank(memories)
        selected = {m.memory_id for m in ranked[:limit]}
        return [m for m in memories if getattr(m, "memory_id", None) in selected]
