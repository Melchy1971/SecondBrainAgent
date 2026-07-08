from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class AgentRetryPolicy:
    max_attempts: int = 2
    retry_on: tuple[type[BaseException], ...] = (RuntimeError, TimeoutError)

    def should_retry(self, attempt: int, error: BaseException) -> bool:
        return attempt < self.max_attempts and isinstance(error, self.retry_on)
