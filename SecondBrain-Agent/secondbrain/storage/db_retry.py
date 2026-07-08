"""Retry for transient database errors. Backend-agnostic, deterministic, testable."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Iterable, TypeVar

T = TypeVar("T")

# transient error class names (matched by type name to avoid importing drivers)
TRANSIENT_NAMES = frozenset({
    "OperationalError", "InterfaceError", "InternalError",
    "DBAPIError", "DisconnectionError", "TimeoutError",
    "ConnectionError", "ConnectionResetError", "BrokenPipeError",
})


def is_transient(exc: BaseException, *, names: Iterable[str] = TRANSIENT_NAMES) -> bool:
    chain = {type(exc).__name__}
    for base in type(exc).__mro__:
        chain.add(base.__name__)
    return bool(chain & set(names))


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 4
    base_delay: float = 0.1
    max_delay: float = 5.0
    multiplier: float = 2.0

    def delay_for(self, attempt: int) -> float:
        return min(self.max_delay, self.base_delay * (self.multiplier ** max(0, attempt)))


def run_with_retry(
    fn: Callable[[], T],
    policy: RetryPolicy | None = None,
    *,
    transient: Callable[[BaseException], bool] = is_transient,
    sleeper: Callable[[float], None] = time.sleep,
) -> T:
    policy = policy or RetryPolicy()
    last: BaseException | None = None
    for attempt in range(policy.max_attempts):
        try:
            return fn()
        except BaseException as exc:  # noqa: BLE001 - re-raised below if not transient/exhausted
            last = exc
            if not transient(exc) or attempt >= policy.max_attempts - 1:
                raise
            sleeper(policy.delay_for(attempt))
    assert last is not None
    raise last
