"""P3 v20.3 - Memory Graph."""

from collections import defaultdict


class MemoryGraph:
    def __init__(self):
        self._edges = defaultdict(set)

    def connect(self, source_id: str, target_id: str):
        self._edges[source_id].add(target_id)

    def neighbors(self, memory_id: str):
        return sorted(self._edges.get(memory_id, set()))

    def degree(self, memory_id: str) -> int:
        return len(self._edges.get(memory_id, set()))
