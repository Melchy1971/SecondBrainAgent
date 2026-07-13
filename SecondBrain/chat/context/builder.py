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
from secondbrain.chat.context.optimization import ContextCandidate, ContextOptimizer
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
        optimizer: ContextOptimizer | None = None,
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
        self.optimizer = optimizer or ContextOptimizer()
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

        # Rank Memory and RAG together, then remove duplicate or conflicting
        # candidates before the existing token-budget stage.
        candidates: list[ContextCandidate] = []
        payloads: dict[str, dict[str, Any]] = {}
        for index, row in enumerate(memories):
            identifier = f"memory:{row.get('memory_id') or row.get('id') or index}"
            text = str(row.get("content") or row.get("text") or "")
            candidates.append(ContextCandidate.from_mapping(identifier, text, "semantic_memory", row))
            payloads[identifier] = row
        for index, row in enumerate(hits):
            identifier = f"document:{row.get('chunk_id') or row.get('document_id') or index}:{index}"
            text = str(row.get("text") or row.get("snippet") or "")
            candidates.append(ContextCandidate.from_mapping(identifier, text, "documents", row))
            payloads[identifier] = row
        optimized = self.optimizer.optimize(prompt, candidates)
        memories = [payloads[row.candidate.id] for row in optimized.ranked if row.candidate.section == "semantic_memory"]
        hits = [payloads[row.candidate.id] for row in optimized.ranked if row.candidate.section == "documents"]

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
            "optimization": optimized.report(),
            "prompt_sections": {name: list(items) for name, items in sections.items()},
        }

    def citations(self, hits: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
        """Kompatibilitaet zum bisherigen ChatContextBuilder.citations-Vertrag."""
        return self.citation_renderer.normalize(hits)
