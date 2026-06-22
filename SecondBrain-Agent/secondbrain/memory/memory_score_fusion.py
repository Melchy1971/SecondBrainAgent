"""P3 v20.4 - Importance + Decay Fusion."""

class MemoryScoreFusion:
    def score(self, importance: float, decay: float) -> float:
        return round((importance * 0.7) + (decay * 0.3), 4)
