"""P3 v20.3 - Recency Decay Engine."""

from time import time


class MemoryDecay:
    def score(self, created_at: float, half_life_days: int = 30) -> float:
        age_days = max(0.0, (time() - created_at) / 86400.0)
        return 1.0 / (1.0 + (age_days / max(1, half_life_days)))
