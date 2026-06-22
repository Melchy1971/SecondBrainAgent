"""P4 v22.2 - Connector Retry and Backoff."""

class ConnectorRetryBackoff:
    def next_delay(self, attempt: int, base: int = 1) -> int:
        return base * (2 ** max(0, attempt))
