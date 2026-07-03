"""v30.46.2 - RetrievalCoordinator: Dokumente, Hybrid Search, Anhaenge, Agenten, Workspace.

Komponiert die bestehende P1-RAG-Runtime (hybrid_search) und den
AttachmentManager. Agent- und Workspace-Kontext sind injizierbare
Provider (Callable[[str, int], list[str]]); ohne Provider leer.
Keine zweite Retrieval-Engine.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Iterable

ContextProvider = Callable[[str, int], list[str]]

DOCUMENT_SOURCES = {"documents", "folders", "ocr", "github", "mail", "csv"}


class RetrievalCoordinator:
    def __init__(
        self,
        project_root: str | Path | None = None,
        *,
        rag_runtime: Any = None,
        attachments: Any = None,
        agent_context: ContextProvider | None = None,
        workspace_context: ContextProvider | None = None,
    ) -> None:
        self.project_root = Path(project_root or Path.cwd()).resolve()
        self._rag_runtime = rag_runtime
        self._attachments = attachments
        self.agent_context = agent_context
        self.workspace_context = workspace_context

    # --- Pipeline-Stufen ------------------------------------------------------

    def documents(
        self,
        query: str,
        *,
        limit: int = 5,
        selected_sources: Iterable[str] = ("documents",),
        selected_documents: Iterable[str] = (),
    ) -> list[dict[str, Any]]:
        """Document Retrieval + Hybrid Search (eine Engine: P1-RAG hybrid_search)."""
        source_set = {str(item).lower() for item in selected_sources}
        if not source_set.intersection(DOCUMENT_SOURCES):
            return []
        result = self._rag().hybrid_search(query, limit=max(limit * 2, limit))
        hits = list(result.get("hits", []))
        selected = {str(item) for item in selected_documents}
        if selected:
            hits = [
                hit
                for hit in hits
                if selected.intersection(
                    {str(hit.get("document_id", "")), str(hit.get("source", "")), str(hit.get("title", ""))}
                )
            ]
        return hits[:limit]

    def attachment_context(self, conversation_id: str | None, *, limit: int = 5) -> list[str]:
        if not conversation_id or self._attachments is None:
            return []
        try:
            manifests = self._attachments.list(conversation_id)
        except Exception:
            return []
        lines = [
            f"Anhang: {manifest.get('name')} ({manifest.get('extension')}, {manifest.get('size')} Bytes)"
            for manifest in manifests[: max(1, int(limit))]
        ]
        return lines

    def agents(self, query: str, *, limit: int = 3) -> list[str]:
        if self.agent_context is None:
            return []
        return list(self.agent_context(query, limit) or [])[:limit]

    def workspace(self, query: str, *, limit: int = 3) -> list[str]:
        if self.workspace_context is None:
            return []
        return list(self.workspace_context(query, limit) or [])[:limit]

    def retrieve(
        self,
        query: str,
        *,
        limit: int = 5,
        selected_sources: Iterable[str] = ("documents",),
        selected_documents: Iterable[str] = (),
        conversation_id: str | None = None,
    ) -> dict[str, Any]:
        return {
            "hits": self.documents(
                query,
                limit=limit,
                selected_sources=selected_sources,
                selected_documents=selected_documents,
            ),
            "attachments": self.attachment_context(conversation_id, limit=limit),
            "agents": self.agents(query),
            "workspace": self.workspace(query),
        }

    # --- intern -----------------------------------------------------------------

    def _rag(self) -> Any:
        if self._rag_runtime is None:
            from secondbrain.p1_rag_runtime import P1RagRuntime

            self._rag_runtime = P1RagRuntime(self.project_root)
        return self._rag_runtime
