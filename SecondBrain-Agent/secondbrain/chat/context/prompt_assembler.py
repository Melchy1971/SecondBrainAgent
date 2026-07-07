"""v30.46.2 - PromptAssembler: Kontext-Sektionen -> LLM-CompletionRequest.

Uebernimmt die Prompt-Konstruktion aus ChatEngine._completion_request
(bleibt dort als Delegation erhalten).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Mapping

from secondbrain.chat.context.limiter import ContextLimiter
from secondbrain.chat.context.optimization import PromptCompressor, PromptExpander
from secondbrain.chat.context.prompt_pipeline import (
    DocumentPrompt,
    FinalPromptBuilder,
    GoalPrompt,
    MemoryPrompt,
    PromptAudit,
    PromptHistory,
    ProviderPrompt,
    SystemPrompt,
    UserPrompt,
    WorkspacePrompt,
)
from secondbrain.chat.context.token_budget import TokenBudgetManager
from secondbrain.providers.base.provider_models import CompletionRequest

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


class PromptAssembler(FinalPromptBuilder):
    def __init__(
        self,
        *,
        budget: TokenBudgetManager | None = None,
        limiter: ContextLimiter | None = None,
        project_root: str | Path | None = None,
        audit: PromptAudit | None = None,
        history: PromptHistory | None = None,
    ) -> None:
        effective_budget = budget or TokenBudgetManager()
        effective_limiter = limiter or ContextLimiter(effective_budget)
        if project_root is not None:
            audit = audit or PromptAudit(project_root)
            history = history or PromptHistory(project_root)
        super().__init__(budget=effective_budget, limiter=effective_limiter, audit=audit, history=history)
        self.compressor = PromptCompressor()
        self.expander = PromptExpander()

    def assemble_context(self, sections: Mapping[str, list[str]]) -> str:
        """Sektionen in Pipeline-Reihenfolge, jeweils budgetiert."""
        parts: list[str] = []
        for name in SECTION_ORDER:
            items = [self.compressor.compress(str(item)) for item in sections.get(name, []) if str(item).strip()]
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
        compress_prompt: bool = False,
        expand_prompt: bool = False,
        context_terms: Iterable[str] = (),
        constraints: Iterable[str] = (),
        provider: str = "",
        provider_prompt: str = "",
        supports_system_prompt: bool = True,
    ) -> CompletionRequest:
        layers = []
        if context:
            system_budget = self.budget.section_budget("system") + self.budget.input_budget // 2
            limited = self.limiter.trim_text(context, max_tokens=system_budget)
            layers.append(SystemPrompt(SYSTEM_CONTEXT_PREFIX + limited))
        if provider_prompt:
            layers.append(ProviderPrompt(provider_prompt))
        effective_prompt = self.compressor.compress(prompt) if compress_prompt else prompt
        if expand_prompt:
            effective_prompt = self.expander.expand(
                effective_prompt,
                context_terms=context_terms,
                constraints=constraints,
            )
        layers.append(UserPrompt(effective_prompt))
        return self.build(
            layers,
            prior,
            model,
            provider=provider,
            stream=stream,
            temperature=temperature,
            history_limit=history_limit,
            supports_system_prompt=supports_system_prompt,
        )

    def final_request(
        self,
        prompt: str,
        prior: Iterable[dict[str, Any]],
        sections: Mapping[str, list[str]],
        model: str,
        *,
        provider: str = "",
        workspace_prompt: str = "",
        goal_prompt: str = "",
        provider_prompt: str = "",
        stream: bool = False,
        temperature: float | None = None,
        history_limit: int = 12,
        supports_system_prompt: bool = True,
    ) -> CompletionRequest:
        """Build the layered request used by the canonical ChatEngine."""
        layers = [SystemPrompt(SYSTEM_CONTEXT_PREFIX.strip())]
        workspace = [workspace_prompt, *sections.get("workspace", []), *sections.get("agents", [])]
        memory = [*sections.get("working_memory", []), *sections.get("semantic_memory", [])]
        documents = [*sections.get("documents", []), *sections.get("attachments", [])]
        if any(str(item).strip() for item in workspace):
            layers.append(WorkspacePrompt("\n".join(str(item) for item in workspace if str(item).strip())))
        if any(str(item).strip() for item in memory):
            layers.append(MemoryPrompt("\n".join(str(item) for item in memory if str(item).strip())))
        if goal_prompt.strip():
            layers.append(GoalPrompt(goal_prompt))
        if any(str(item).strip() for item in documents):
            layers.append(DocumentPrompt("\n".join(str(item) for item in documents if str(item).strip())))
        if provider_prompt.strip():
            layers.append(ProviderPrompt(provider_prompt))
        layers.append(UserPrompt(prompt))
        return self.build(
            layers,
            prior,
            model,
            provider=provider,
            stream=stream,
            temperature=temperature,
            history_limit=history_limit,
            supports_system_prompt=supports_system_prompt,
        )
