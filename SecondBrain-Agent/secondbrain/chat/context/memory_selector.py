"""v30.46.2 - MemorySelector: Conversation-, Working- und Semantic Memory.

Komponiert ausschliesslich Bestandsmodule (MemoryExplorer, MemoryRanker,
SemanticMemorySearch). Keine zweite Memory-Engine.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from secondbrain.memory.memory_ranker import MemoryRanker
from secondbrain.memory.semantic_search import SemanticMemorySearch


class MemorySelector:
    def __init__(
        self,
        project_root: str | Path | None = None,
        *,
        memory_explorer: Any = None,
        ranker: MemoryRanker | None = None,
        semantic_search: SemanticMemorySearch | None = None,
    ) -> None:
        self.project_root = Path(project_root or Path.cwd()).resolve()
        self._memory_explorer = memory_explorer
        self.ranker = ranker or MemoryRanker()
        self.semantic_search = semantic_search or SemanticMemorySearch()

    # --- Pipeline-Stufen ------------------------------------------------------

    def conversation(self, history: Iterable[dict[str, Any]], *, limit: int = 12) -> list[dict[str, Any]]:
        rows = [dict(row) for row in history or []]
        return rows[-max(1, int(limit)):]

    def working(self, items: Iterable[Any], *, limit: int = 5) -> list[str]:
        """Working Memory: aktuelle Arbeitskontext-Eintraege, Ranking via MemoryRanker."""
        pool = list(items or [])
        if not pool:
            return []
        ranked = self.ranker.rank(pool)
        selected_ids = {score.memory_id for score in ranked[: max(1, int(limit))]}
        result: list[str] = []
        for item in pool:
            identifier = getattr(item, "memory_id", None)
            if identifier is not None and identifier not in selected_ids:
                continue
            text = getattr(item, "text", None) or getattr(item, "content", None) or str(item)
            result.append(str(text))
            if len(result) >= limit:
                break
        return result

    def semantic(self, query: str, *, limit: int = 5) -> list[dict[str, Any]]:
        """Semantic Memory ueber den bestehenden MemoryExplorer."""
        memory = self._memory()
        if memory is None:
            return []
        result = memory.search(query, limit=limit)
        return list(result.get("memories", []))

    def select(
        self,
        query: str,
        history: Iterable[dict[str, Any]],
        *,
        working_items: Iterable[Any] = (),
        limit: int = 5,
        conversation_limit: int = 12,
        include_memory: bool = True,
    ) -> dict[str, list[Any]]:
        return {
            "conversation": self.conversation(history, limit=conversation_limit),
            "working": self.working(working_items, limit=limit) if include_memory else [],
            "semantic": self.semantic(query, limit=limit) if include_memory else [],
        }

    # --- intern -----------------------------------------------------------------

    def _memory(self) -> Any:
        if self._memory_explorer is None:
            try:
                from secondbrain.native.memory_explorer import MemoryExplorer

                self._memory_explorer = MemoryExplorer(self.project_root)
            except Exception:
                return None
        return self._memory_explorer
