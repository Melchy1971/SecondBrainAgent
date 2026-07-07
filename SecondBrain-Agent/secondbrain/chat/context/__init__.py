"""v30.46.2 - Eine Context Pipeline fuer alle Chat-Oberflaechen.

Pipeline (Reihenfolge fix):

    Prompt
      -> Conversation Memory
      -> Working Memory
      -> Semantic Memory
      -> Document Retrieval
      -> Hybrid Search
      -> Context Builder
      -> LLM (CompletionRequest via PromptAssembler)

Kontextquellen: Conversation, Memory, RAG, Dokumente, Anhaenge,
Agenten, Workspace (Agent/Workspace als injizierbare Provider).

Konsolidiert die P3-Stubs (memory/context_builder.py,
context_assembly_pipeline.py, context_window_manager.py) und den
ChatContextBuilder aus secondbrain.native.chat. Keine zweite
Retrieval- oder Memory-Engine: MemorySelector und
RetrievalCoordinator komponieren ausschliesslich Bestandsmodule.
"""
from __future__ import annotations

import importlib
from typing import Any

_EXPORTS = {
    "ContextBuilder": "secondbrain.chat.context.builder",
    "PromptAssembler": "secondbrain.chat.context.prompt_assembler",
    "MemorySelector": "secondbrain.chat.context.memory_selector",
    "RetrievalCoordinator": "secondbrain.chat.context.retrieval",
    "ContextLimiter": "secondbrain.chat.context.limiter",
    "TokenBudgetManager": "secondbrain.chat.context.token_budget",
    "ContextCandidate": "secondbrain.chat.context.optimization",
    "ContextOptimizer": "secondbrain.chat.context.optimization",
    "ContextRanker": "secondbrain.chat.context.optimization",
    "SourceRanker": "secondbrain.chat.context.optimization",
    "DuplicateRemover": "secondbrain.chat.context.optimization",
    "ConflictResolver": "secondbrain.chat.context.optimization",
    "PromptCompressor": "secondbrain.chat.context.optimization",
    "PromptExpander": "secondbrain.chat.context.optimization",
    "PromptLayer": "secondbrain.chat.context.prompt_pipeline",
    "SystemPrompt": "secondbrain.chat.context.prompt_pipeline",
    "WorkspacePrompt": "secondbrain.chat.context.prompt_pipeline",
    "MemoryPrompt": "secondbrain.chat.context.prompt_pipeline",
    "GoalPrompt": "secondbrain.chat.context.prompt_pipeline",
    "DocumentPrompt": "secondbrain.chat.context.prompt_pipeline",
    "UserPrompt": "secondbrain.chat.context.prompt_pipeline",
    "ProviderPrompt": "secondbrain.chat.context.prompt_pipeline",
    "FinalPromptBuilder": "secondbrain.chat.context.prompt_pipeline",
    "PromptAudit": "secondbrain.chat.context.prompt_pipeline",
    "PromptHistory": "secondbrain.chat.context.prompt_pipeline",
}

__all__ = sorted(_EXPORTS)


def __getattr__(name: str) -> Any:
    module_name = _EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module 'secondbrain.chat.context' has no attribute {name!r}")
    return getattr(importlib.import_module(module_name), name)


def __dir__() -> list[str]:
    return __all__
