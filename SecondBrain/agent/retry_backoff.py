"""P2 v21.3 - Retry and Backoff Engine."""

class RetryBackoffEngine:
    def schedule(self, attempt: int, base_delay_seconds: int = 1) -> int:
        attempt = max(0, attempt)
        return base_delay_seconds * (2 ** attempt)
