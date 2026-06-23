"""v30.0 in-memory provider rate limiter."""
from __future__ import annotations

from collections import deque
from time import time


class ProviderRateLimiter:
    def __init__(self, max_calls: int = 60, window_seconds: int = 60) -> None:
        self.max_calls = max_calls
        self.window_seconds = window_seconds
        self._calls: dict[str, deque[float]] = {}

    def allow(self, provider: str) -> bool:
        now = time()
        calls = self._calls.setdefault(provider, deque())
        while calls and now - calls[0] > self.window_seconds:
            calls.popleft()
        if len(calls) >= self.max_calls:
            return False
        calls.append(now)
        return True
