"""v30.46.2 - ContextLimiter: kuerzt Kontext auf Sektionsbudgets.

Ersetzt memory/context_window_manager.ContextWindowManager (bleibt Shim).
"""
from __future__ import annotations

from typing import Iterable, Mapping

from secondbrain.chat.context.token_budget import TokenBudgetManager

ELLIPSIS = " …[gekuerzt]"


class ContextLimiter:
    def __init__(self, budget: TokenBudgetManager | None = None) -> None:
        self.budget = budget or TokenBudgetManager()

    def trim_items(self, texts: Iterable[str], *, max_chars: int) -> list[str]:
        """Ganze Eintraege bis zur Zeichen-Grenze (Kontrakt des alten trim())."""
        result: list[str] = []
        size = 0
        for text in texts:
            length = len(text)
            if size + length > max_chars:
                break
            result.append(text)
            size += length
        return result

    def trim_text(self, text: str, *, max_tokens: int) -> str:
        limit = TokenBudgetManager.estimate_chars(max_tokens)
        if len(text or "") <= limit:
            return text or ""
        cut = max(0, limit - len(ELLIPSIS))
        return (text or "")[:cut] + ELLIPSIS

    def limit_section(self, section: str, items: Iterable[str]) -> list[str]:
        pool = list(items)
        budget_tokens = self.budget.section_budget(section)
        max_chars = TokenBudgetManager.estimate_chars(budget_tokens)
        kept = self.trim_items(pool, max_chars=max_chars)
        if not kept and pool and pool[0]:
            kept = [self.trim_text(pool[0], max_tokens=budget_tokens)]
        return kept

    def limit_sections(self, sections: Mapping[str, list[str]]) -> dict[str, list[str]]:
        return {name: self.limit_section(name, items) for name, items in sections.items()}
