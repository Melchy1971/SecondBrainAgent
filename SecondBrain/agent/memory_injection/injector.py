"""v30.64 Agent Memory Injection - MemoryInjector.

Turns the existing memory store into a bounded, auditable context for an agent.
Pipeline (order matters - the hard safety gates run first):

    candidates -> drop secrets -> drop privacy (if privacy mode)
      -> enforce source rule -> rank -> apply relevance floor
      -> fit into token budget (and count limit) -> detect conflicts
      -> MemoryContext

The store is the canonical ``secondbrain.agent.memory`` store (or anything
exposing ``list``/``search``). No memory is stored or duplicated here.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from .audit import MemoryInjectionAudit
from .budget import MemoryBudget, estimate_tokens
from .conflicts import MemoryConflictDetector
from .filters import has_explicit_source, is_secret, privacy_excluded, source_of
from .models import (
    EXCLUDE_BUDGET,
    EXCLUDE_LOW_RELEVANCE,
    EXCLUDE_NO_SOURCE,
    EXCLUDE_PRIVACY,
    EXCLUDE_SECRET,
    MemoryContext,
    MemoryEvidence,
    MemoryExclusion,
    MemoryQuery,
)
from .ranking import MemoryRanking


def _enum_value(value: Any) -> str:
    return str(getattr(value, "value", value))


class MemoryInjector:
    def __init__(
        self,
        store: Any,
        *,
        ranking: MemoryRanking | None = None,
        conflict_detector: MemoryConflictDetector | None = None,
        audit: MemoryInjectionAudit | None = None,
    ):
        self.store = store
        self.ranking = ranking or MemoryRanking()
        self.conflicts = conflict_detector or MemoryConflictDetector()
        self.audit = audit

    @classmethod
    def for_project(cls, project_root: str | Path, store: Any, **kwargs: Any) -> "MemoryInjector":
        return cls(store, audit=MemoryInjectionAudit(project_root), **kwargs)

    # -- candidate gathering ----------------------------------------------
    def _candidates(self, query: MemoryQuery) -> list[Any]:
        if hasattr(self.store, "list"):
            records = list(self.store.list())
        elif hasattr(self.store, "search"):
            records = list(self.store.search(query.text or "", limit=1000))
        else:
            records = list(self.store)
        if query.workspace_id:
            records = [r for r in records
                       if getattr(r, "workspace_id", None) in (query.workspace_id, None)]
        return records

    # -- core --------------------------------------------------------------
    def preview(self, query: MemoryQuery, *, now: datetime | None = None) -> MemoryContext:
        exclusions: list[MemoryExclusion] = []
        candidates = self._candidates(query)

        # 1) secrets are never injected
        surviving: list[Any] = []
        for rec in candidates:
            secret, detail = is_secret(rec)
            if secret:
                exclusions.append(MemoryExclusion(rec.memory_id, EXCLUDE_SECRET, detail))
            else:
                surviving.append(rec)

        # 2) privacy mode withholds private/personal memories
        after_privacy: list[Any] = []
        for rec in surviving:
            excluded, detail = privacy_excluded(rec, query.privacy_mode)
            if excluded:
                exclusions.append(MemoryExclusion(rec.memory_id, EXCLUDE_PRIVACY, detail))
            else:
                after_privacy.append(rec)

        # 3) source obligation (Quellenpflicht)
        sourced: list[Any] = []
        for rec in after_privacy:
            if query.require_source and not has_explicit_source(rec):
                exclusions.append(MemoryExclusion(rec.memory_id, EXCLUDE_NO_SOURCE,
                                                  "explicit source required"))
            else:
                sourced.append(rec)

        # 4) rank, then apply relevance floor
        ranked = self.ranking.rank(sourced, query.text, now=now)
        floor = query.min_relevance
        relevant: list[Any] = []
        for rm in ranked:
            drop_zero = bool(query.text) and rm.relevance <= 0.0
            if rm.relevance < floor or drop_zero:
                exclusions.append(MemoryExclusion(rm.record.memory_id, EXCLUDE_LOW_RELEVANCE,
                                                  f"relevance={rm.relevance:.2f}"))
            else:
                relevant.append(rm)

        # 5) fit into token budget and count limit
        budget = MemoryBudget(max_tokens=query.token_budget)
        evidences: list[MemoryEvidence] = []
        selected_records: list[Any] = []
        for rm in relevant:
            if len(evidences) >= query.limit:
                exclusions.append(MemoryExclusion(rm.record.memory_id, EXCLUDE_BUDGET,
                                                  "count_limit_reached"))
                continue
            text = rm.record.text
            if not budget.can_fit(text):
                exclusions.append(MemoryExclusion(rm.record.memory_id, EXCLUDE_BUDGET,
                                                  f"tokens={estimate_tokens(text)}, "
                                                  f"remaining={budget.remaining}"))
                continue
            tokens = budget.add(text)
            evidences.append(MemoryEvidence(
                memory_id=rm.record.memory_id,
                text=text,
                source=source_of(rm.record),
                confidence=round(rm.confidence, 4),
                recency_days=rm.recency_days,
                scope=_enum_value(getattr(rm.record, "scope", "")),
                visibility=_enum_value(getattr(rm.record, "visibility", "")),
                relevance=round(rm.relevance, 4),
                score=round(rm.score, 4),
                tokens=tokens,
                tags=tuple(getattr(rm.record, "tags", ()) or ()),
            ))
            selected_records.append(rm.record)

        # 6) conflicts among what the agent actually receives
        conflicts = self.conflicts.detect(selected_records)

        return MemoryContext(
            query=query,
            evidences=evidences,
            exclusions=exclusions,
            conflicts=conflicts,
            budget_limit=query.token_budget,
            tokens_used=budget.used,
            privacy_mode=query.privacy_mode,
        )

    def inject(self, query: MemoryQuery, *, actor: str = "agent", agent_id: str = "",
               now: datetime | None = None) -> MemoryContext:
        context = self.preview(query, now=now)
        if self.audit is not None:
            self.audit.record(actor=actor, agent_id=agent_id, context=context)
        return context
