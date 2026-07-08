"""P3 v20.1 - Memory Ranking Engine."""

from __future__ import annotations

from dataclasses import dataclass
from time import time


@dataclass(frozen=True)
class MemoryScore:
    memory_id: str
    score: float


class MemoryRanker:
    def rank(self, items):
        now = time()
        scored = []
        for item in items:
            created = getattr(item, "created_at", now)
            recency = max(1.0, now - created)
            base = float(getattr(item, "score", 1.0))
            scored.append(
                MemoryScore(
                    memory_id=getattr(item, "memory_id", "unknown"),
                    score=base + (1.0 / recency),
                )
            )
        return sorted(scored, key=lambda x: x.score, reverse=True)
