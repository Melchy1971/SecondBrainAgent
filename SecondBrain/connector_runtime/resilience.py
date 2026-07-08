"""Retry/backoff, rate limiting, and the dead-letter queue."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from secondbrain.connector_runtime.models import (
    ConnectorError,
    DeadLetter,
    PermanentError,
    RateLimitError,
    TransientError,
)


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 4
    base_delay: float = 0.5
    max_delay: float = 30.0
    factor: float = 2.0


def run_with_retry(
    fn: Callable[[], Any],
    policy: RetryPolicy | None = None,
    *,
    sleeper: Callable[[float], None] = time.sleep,
) -> Any:
    """Run ``fn`` with exponential backoff.

    Retries ``TransientError``/``RateLimitError`` (honoring ``retry_after``).
    ``PermanentError`` and ``AuthError`` are raised immediately - they must not
    burn retries and should be dead-lettered by the caller.
    """
    policy = policy or RetryPolicy()
    last: BaseException | None = None
    for attempt in range(1, policy.max_attempts + 1):
        try:
            return fn()
        except RateLimitError as exc:
            last = exc
            backoff = min(policy.max_delay, policy.base_delay * (policy.factor ** (attempt - 1)))
            if attempt < policy.max_attempts:
                sleeper(max(exc.retry_after, backoff))
        except TransientError as exc:
            last = exc
            if attempt < policy.max_attempts:
                sleeper(min(policy.max_delay, policy.base_delay * (policy.factor ** (attempt - 1))))
        except (PermanentError, ConnectorError):
            raise
    raise TransientError(f"retry_exhausted after {policy.max_attempts} attempts: {last}")


class RateLimiter:
    """Simple token bucket. Injectable clock/sleeper keep it deterministic in tests."""

    def __init__(self, rate_per_sec: float, capacity: float | None = None, *,
                 clock: Callable[[], float] = time.monotonic,
                 sleeper: Callable[[float], None] = time.sleep) -> None:
        self.rate = float(rate_per_sec)
        self.capacity = float(capacity if capacity is not None else rate_per_sec)
        self._tokens = self.capacity
        self._clock = clock
        self._sleeper = sleeper
        self._last = clock()

    def _refill(self) -> None:
        now = self._clock()
        elapsed = max(0.0, now - self._last)
        self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)
        self._last = now

    def acquire(self, tokens: float = 1.0) -> float:
        self._refill()
        waited = 0.0
        if self._tokens < tokens:
            need = (tokens - self._tokens) / self.rate if self.rate > 0 else 0.0
            self._sleeper(need)
            waited = need
            self._refill()
        self._tokens -= tokens
        return waited


class DeadLetterQueue:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def add(self, dead_letter: DeadLetter) -> DeadLetter:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(dead_letter.to_dict(), ensure_ascii=False, sort_keys=True) + "\n")
        return dead_letter

    def entries(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        return [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def count(self) -> int:
        return len(self.entries())

    def clear(self) -> None:
        if self.path.exists():
            self.path.unlink()
