"""v30.64 Agent Memory Injection - MemoryBudget.

A deliberately simple, deterministic token estimator (~4 characters per token)
so injection is bounded and reproducible. The point is not exact tokenization but
a hard, auditable ceiling on how much memory an agent can pull in.
"""

from __future__ import annotations

from dataclasses import dataclass

CHARS_PER_TOKEN = 4


def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, (len(text) + CHARS_PER_TOKEN - 1) // CHARS_PER_TOKEN)


@dataclass
class MemoryBudget:
    max_tokens: int | None = None
    used: int = 0

    @property
    def unlimited(self) -> bool:
        return self.max_tokens is None

    @property
    def remaining(self) -> int | None:
        if self.max_tokens is None:
            return None
        return max(0, self.max_tokens - self.used)

    def can_fit(self, text: str) -> bool:
        if self.max_tokens is None:
            return True
        return self.used + estimate_tokens(text) <= self.max_tokens

    def add(self, text: str) -> int:
        cost = estimate_tokens(text)
        self.used += cost
        return cost
