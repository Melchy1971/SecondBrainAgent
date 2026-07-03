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
}

__all__ = sorted(_EXPORTS)


def __getattr__(name: str) -> Any:
    module_name = _EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module 'secondbrain.chat.context' has no attribute {name!r}")
    return getattr(importlib.import_module(module_name), name)


def __dir__() -> list[str]:
    return __all__
