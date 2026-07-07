"""v30.68 Reasoning Engine - EvidenceCollector.

Gathers evidence for a reasoning session from the existing subsystems and ranks
it. Memory evidence is pulled through the v30.64 ``MemoryInjector`` (so it keeps
its source, confidence and recency and honours secrets/privacy), RAG evidence
through an injected search callable, and manual evidence directly. Conflict
detection reuses the v30.64 ``MemoryConflictDetector``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from .models import NEUTRAL, Evidence, new_id


class EvidenceCollector:
    def __init__(
        self,
        project_root: str | Path | None = None,
        *,
        memory_store: Any | None = None,
        memory_injector: Any | None = None,
        rag_search: Callable[[str, int], list[dict]] | None = None,
    ):
        self.project_root = Path(project_root).resolve() if project_root else None
        self.memory_store = memory_store
        self._memory_injector = memory_injector
        self.rag_search = rag_search
        self._manual: list[Evidence] = []

    # -- manual ------------------------------------------------------------
    def add(self, evidence: Evidence) -> Evidence:
        self._manual.append(evidence)
        return evidence

    def add_fact(self, text: str, *, source: str, confidence: float = 0.6, stance: str = NEUTRAL,
                 target: str = "", metadata: dict | None = None) -> Evidence:
        return self.add(Evidence.create(text, source=source, confidence=confidence, stance=stance,
                                        target=target, ref="manual", metadata=metadata))

    # -- memory (reuse v30.64 MemoryInjector) ------------------------------
    def _injector(self):
        if self._memory_injector is not None:
            return self._memory_injector
        if self.memory_store is None:
            return None
        from secondbrain.agent.memory_injection import MemoryInjector
        self._memory_injector = MemoryInjector(self.memory_store)
        return self._memory_injector

    def collect_from_memory(self, query: str, *, limit: int = 10, privacy_mode: bool = False) -> list[Evidence]:
        injector = self._injector()
        if injector is None:
            return []
        from secondbrain.agent.memory_injection import MemoryQuery
        ctx = injector.preview(MemoryQuery(text=query, limit=limit, privacy_mode=privacy_mode,
                                           require_source=False))
        out: list[Evidence] = []
        for ev in ctx.evidences:
            out.append(Evidence(
                id=new_id("ev"), text=ev.text, source=ev.source, confidence=ev.confidence,
                stance=NEUTRAL, recency_days=ev.recency_days, ref=f"memory:{ev.memory_id}",
                metadata={"relevance": ev.relevance},
            ))
        return out

    # -- rag (injected search) --------------------------------------------
    def collect_from_rag(self, query: str, *, limit: int = 5) -> list[Evidence]:
        if self.rag_search is None:
            return []
        rows = self.rag_search(query, limit) or []
        out: list[Evidence] = []
        for row in rows:
            out.append(Evidence(
                id=new_id("ev"), text=str(row.get("text", "")),
                source=str(row.get("source", "rag")), confidence=float(row.get("score", 0.5)),
                stance=NEUTRAL, ref=f"rag:{row.get('id', '')}",
            ))
        return out

    # -- collect + rank + conflicts ---------------------------------------
    def collect(self, query: str, *, limit: int = 10, privacy_mode: bool = False,
                include_manual: bool = True) -> list[Evidence]:
        evidence = self.collect_from_memory(query, limit=limit, privacy_mode=privacy_mode)
        evidence += self.collect_from_rag(query, limit=limit)
        if include_manual:
            evidence += list(self._manual)
        return self.rank(evidence)

    @staticmethod
    def rank(evidence: list[Evidence]) -> list[Evidence]:
        # Highest confidence first; recent before old on ties.
        return sorted(evidence, key=lambda e: (e.confidence, -e.recency_days), reverse=True)

    @staticmethod
    def detect_conflicts(evidence: list[Evidence]) -> list[dict[str, Any]]:
        from secondbrain.agent.memory_injection import MemoryConflictDetector
        conflicts = MemoryConflictDetector().detect(evidence)
        return [c.to_dict() for c in conflicts]
