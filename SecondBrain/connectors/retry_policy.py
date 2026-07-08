"""P1.2.2 - Retry policy for connector operations.

The policy is intentionally side-effect free. It classifies retryable failures,
calculates deterministic backoff values, and lets runners decide whether to
sleep, log, or short-circuit. Tests can therefore validate retry behaviour
without waiting.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Type


DEFAULT_RETRYABLE_EXCEPTIONS: tuple[Type[BaseException], ...] = (
    TimeoutError,
    ConnectionError,
)


@dataclass(frozen=True)
class RetryDecision:
    should_retry: bool
    attempt: int
    max_attempts: int
    delay_seconds: float
    reason: str


@dataclass(frozen=True)
class RetryPolicy:
    """Deterministic retry policy for connector fetch and item processing.

    max_attempts counts the initial attempt. A value of 3 means: first attempt
    plus two retries. No sleeping happens inside this class.
    """

    max_attempts: int = 3
    base_delay_seconds: float = 0.25
    max_delay_seconds: float = 5.0
    retryable_exceptions: tuple[Type[BaseException], ...] = field(
        default_factory=lambda: DEFAULT_RETRYABLE_EXCEPTIONS
    )

    def __post_init__(self) -> None:
        if self.max_attempts <= 0:
            raise ValueError("max_attempts must be > 0")
        if self.base_delay_seconds < 0:
            raise ValueError("base_delay_seconds must be >= 0")
        if self.max_delay_seconds < 0:
            raise ValueError("max_delay_seconds must be >= 0")

    @classmethod
    def for_exceptions(
        cls,
        exceptions: Iterable[Type[BaseException]],
        *,
        max_attempts: int = 3,
        base_delay_seconds: float = 0.25,
        max_delay_seconds: float = 5.0,
    ) -> "RetryPolicy":
        return cls(
            max_attempts=max_attempts,
            base_delay_seconds=base_delay_seconds,
            max_delay_seconds=max_delay_seconds,
            retryable_exceptions=tuple(exceptions),
        )

    def delay_for_attempt(self, attempt: int) -> float:
        if attempt <= 1:
            return 0.0
        delay = self.base_delay_seconds * (2 ** (attempt - 2))
        return min(delay, self.max_delay_seconds)

    def classify(self, exc: BaseException, *, attempt: int) -> RetryDecision:
        retryable = isinstance(exc, self.retryable_exceptions)
        can_retry = retryable and attempt < self.max_attempts
        reason = "retryable" if retryable else "non_retryable"
        if retryable and not can_retry:
            reason = "attempts_exhausted"
        return RetryDecision(
            should_retry=can_retry,
            attempt=attempt,
            max_attempts=self.max_attempts,
            delay_seconds=self.delay_for_attempt(attempt + 1) if can_retry else 0.0,
            reason=reason,
        )
