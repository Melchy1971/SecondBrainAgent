"""P3 v20.1 - Forgetting Policies."""

from time import time


class ForgettingPolicy:
    def should_archive(self, created_at: float, max_age_seconds: int = 86400 * 30) -> bool:
        return (time() - created_at) > max_age_seconds
