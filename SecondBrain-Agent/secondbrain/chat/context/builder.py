"""v30.46.2 - ContextBuilder: die eine Context Pipeline.

Orchestriert: Prompt -> Conversation Memory -> Working Memory ->
Semantic Memory -> Document Retrieval -> Hybrid Search -> Context ->
LLM-Request (PromptAssembler).

Kompatibel zum bisherigen ChatContextBuilder-Vertrag
(build() -> {context, conversation, memories, hits, citations});
zusaetzlich liefert build() einen Budget-Report.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from secondbrain.chat.citations import CitationRenderer
from secondbrain.chat.context.limiter import ContextLimiter
from secondbrain.chat.context.memory_selector import MemorySelector
from secondbrain.chat.context.prompt_assembler import PromptAssembler
from secondbrain.chat.context.retrieval import RetrievalCoordinator
from secondbrain.chat.context.token_budget import TokenBudgetManager


class ContextBuilder:
    def __init__(
        self,
        project_root: str | Path | None = None,
        *,
        rag_runtime: Any = None,
        memory_explorer: Any = None,
        attachments: Any = None,
        agent_context: Any = None,
        workspace_context: Any = None,
        budget: TokenBudgetManager | None = None,
    ) -> None:
        self.project_root = Path(project_root or Path.cwd()).resolve()
        self.budget = budget or TokenBudgetManager()
        self.limiter = ContextLimiter(self.budget)
        self.selector = MemorySelector(self.project_root, memory_explorer=memory_explorer)
        self.retrieval = RetrievalCoordinator(
            self.project_root,
            rag_runtime=rag_runtime,
            attachments=attachments,
            agent_context=agent_context,
            workspace_context=workspace_context,
        )
        self.assembler = PromptAssembler(budget=self.budget, limiter=self.limiter)
        self.citation_renderer = CitationRenderer()

    def build(
        self,
        prompt: str,
        history: list[dict[str, Any]],
        *,
        selected_sources: Iterable[str] = ("documents", "memory"),
        selected_documents: Iterable[str] = (),
        limit: int = 5,
        conversation_id: str | None = None,
        working_items: Iterable[Any] = (),
    ) -> dict[str, Any]:
        source_set = {str(item).lower() for item in selected_sources}
        include_memory = "memory" in source_set

        # 1-3: Conversation -> Working -> Semantic Memory
        memory = self.selector.select(
            prompt,
            history,
            working_items=working_items,
            limit=limit,
            include_memory=include_memory,
        )
        conversation = memory["conversation"]
        working = memory["working"]
        memories = memory["semantic"]

        # 4-5: Document Retrieval + Hybrid Search (+ Anhaenge, Agenten, Workspace)
        retrieved = self.retrieval.retrieve(
            prompt,
            limit=limit,
            selected_sources=source_set,
            selected_documents=selected_documents,
            conversation_id=conversation_id,
        )
        hits = retrieved["hits"]

        # 6: Context Builder (budgetierte Sektionen in Pipeline-Reihenfolge)
        sections: dict[str, list[str]] = {
            "conversation": [f"{row.get('role')}: {row.get('content')}" for row in conversation],
            "working_memory": list(working),
            "semantic_memory": [str(row.get("content", "")) for row in memories],
            "documents": [str(row.get("text") or row.get("snippet") or "") for row in hits],
            "attachments": retrieved["attachments"],
            "agents": retrieved["agents"],
            "workspace": retrieved["workspace"],
        }
        context = self.assembler.assemble_context(sections)
        citations = self.citation_renderer.normalize(hits)

        return {
            "context": context,
            "conversation": conversation,
            "memories": memories,
            "working_memory": working,
            "hits": hits,
            "citations": citations,
            "budget": self.budget.allocate(
                {name: "\n".join(items) for name, items in sections.items()}
            ),
        }

    def citations(self, hits: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
        """Kompatibilitaet zum bisherigen ChatContextBuilder.citations-Vertrag."""
        return self.citation_renderer.normalize(hits)
