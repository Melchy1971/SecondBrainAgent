"""v30.46.2 - TokenBudgetManager: Budgetierung des LLM-Kontextfensters.

Dependency-frei; Token-Schaetzung ueber Zeichenheuristik (~4 Zeichen/Token).
Budgets werden pro Sektion der Context Pipeline vergeben.
"""
from __future__ import annotations

import math
from typing import Any, Mapping

DEFAULT_SHARES: dict[str, float] = {
    "system": 0.05,
    "conversation": 0.30,
    "working_memory": 0.10,
    "semantic_memory": 0.15,
    "documents": 0.25,
    "attachments": 0.10,
    "agents": 0.025,
    "workspace": 0.025,
}


class TokenBudgetManager:
    CHARS_PER_TOKEN = 4.0

    def __init__(
        self,
        max_tokens: int = 8192,
        *,
        reserved_output_tokens: int = 1024,
        shares: Mapping[str, float] | None = None,
    ) -> None:
        self.max_tokens = max(512, int(max_tokens))
        self.reserved_output_tokens = max(0, int(reserved_output_tokens))
        raw = dict(shares or DEFAULT_SHARES)
        total = sum(raw.values()) or 1.0
        self.shares = {name: value / total for name, value in raw.items()}

    @property
    def input_budget(self) -> int:
        return max(256, self.max_tokens - self.reserved_output_tokens)

    @classmethod
    def estimate_tokens(cls, text: str) -> int:
        return math.ceil(len(text or "") / cls.CHARS_PER_TOKEN)

    @classmethod
    def estimate_chars(cls, tokens: int) -> int:
        return int(max(0, tokens) * cls.CHARS_PER_TOKEN)

    def section_budget(self, section: str) -> int:
        share = self.shares.get(section)
        if share is None:
            share = 0.05
        return max(64, int(self.input_budget * share))

    def fits(self, text: str, section: str) -> bool:
        return self.estimate_tokens(text) <= self.section_budget(section)

    def allocate(self, sections: Mapping[str, str]) -> dict[str, Any]:
        report: dict[str, Any] = {"input_budget": self.input_budget, "sections": {}}
        used = 0
        for name, text in sections.items():
            tokens = self.estimate_tokens(text)
            budget = self.section_budget(name)
            used += min(tokens, budget)
            report["sections"][name] = {
                "tokens": tokens,
                "budget": budget,
                "over_budget": tokens > budget,
            }
        report["used"] = used
        report["remaining"] = max(0, self.input_budget - used)
        return report
