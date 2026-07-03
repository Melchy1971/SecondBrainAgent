"""v30.46.2 - PromptAssembler: Kontext-Sektionen -> LLM-CompletionRequest.

Uebernimmt die Prompt-Konstruktion aus ChatEngine._completion_request
(bleibt dort als Delegation erhalten).
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping

from secondbrain.chat.context.limiter import ContextLimiter
from secondbrain.chat.context.token_budget import TokenBudgetManager
from secondbrain.providers.base.provider_models import ChatMessage, CompletionRequest

SYSTEM_CONTEXT_PREFIX = (
    "Nutze ausschließlich den folgenden SecondBrain-Kontext und belege Aussagen mit Quellen.\n\n"
)

SECTION_TITLES = {
    "conversation": "Conversation Memory:",
    "working_memory": "Working Memory:",
    "semantic_memory": "Semantic/Working Memory:",
    "documents": "Document Retrieval / Hybrid Search:",
    "attachments": "Anhaenge:",
    "agents": "Agenten-Kontext:",
    "workspace": "Workspace-Kontext:",
}

SECTION_ORDER = (
    "conversation",
    "working_memory",
    "semantic_memory",
    "documents",
    "attachments",
    "agents",
    "workspace",
)


class PromptAssembler:
    def __init__(
        self,
        *,
        budget: TokenBudgetManager | None = None,
        limiter: ContextLimiter | None = None,
    ) -> None:
        self.budget = budget or TokenBudgetManager()
        self.limiter = limiter or ContextLimiter(self.budget)

    def assemble_context(self, sections: Mapping[str, list[str]]) -> str:
        """Sektionen in Pipeline-Reihenfolge, jeweils budgetiert."""
        parts: list[str] = []
        for name in SECTION_ORDER:
            items = [str(item) for item in sections.get(name, []) if str(item).strip()]
            if not items:
                continue
            kept = self.limiter.limit_section(name, items)
            if kept:
                parts.append(SECTION_TITLES[name] + "\n" + "\n".join(kept))
        return "\n\n".join(parts)

    def completion_request(
        self,
        prompt: str,
        prior: Iterable[dict[str, Any]],
        context: str,
        model: str,
        *,
        stream: bool,
        temperature: float | None = None,
        history_limit: int = 12,
    ) -> CompletionRequest:
        messages: list[ChatMessage] = []
        if context:
            system_budget = self.budget.section_budget("system") + self.budget.input_budget // 2
            limited = self.limiter.trim_text(context, max_tokens=system_budget)
            messages.append(ChatMessage("system", SYSTEM_CONTEXT_PREFIX + limited))
        rows = list(prior)[-history_limit:]
        for row in rows:
            role = str(row.get("role") or "user")
            if role in {"system", "user", "assistant", "tool"}:
                messages.append(ChatMessage(role, str(row.get("content") or "")))
        messages.append(ChatMessage("user", prompt))
        extra: dict[str, Any] = {}
        if temperature is not None:
            extra["temperature"] = float(temperature)
        return CompletionRequest(model=model, messages=messages, stream=stream, **extra)
