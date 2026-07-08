"""v30.64 Agent Memory Injection - value objects.

These describe *what an agent receives*: the query, each injected memory with its
source/confidence/recency, everything excluded (and why), detected conflicts and
the token-budget accounting. The underlying records come from the existing
``secondbrain.agent.memory`` store - this layer never stores memories itself.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

# Exclusion reasons.
EXCLUDE_SECRET = "secret"
EXCLUDE_PRIVACY = "privacy_mode"
EXCLUDE_BUDGET = "token_budget"
EXCLUDE_NO_SOURCE = "no_source"
EXCLUDE_LOW_RELEVANCE = "low_relevance"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class MemoryQuery:
    text: str = ""
    workspace_id: str | None = None
    limit: int = 10
    privacy_mode: bool = False
    token_budget: int | None = None
    tags: tuple[str, ...] = ()
    require_source: bool = True
    min_relevance: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "workspace_id": self.workspace_id,
            "limit": self.limit,
            "privacy_mode": self.privacy_mode,
            "token_budget": self.token_budget,
            "tags": list(self.tags),
            "require_source": self.require_source,
            "min_relevance": self.min_relevance,
        }


@dataclass(frozen=True)
class MemoryEvidence:
    memory_id: str
    text: str
    source: str
    confidence: float
    recency_days: int
    scope: str
    visibility: str
    relevance: float
    score: float
    tokens: int
    tags: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["tags"] = list(self.tags)
        return data


@dataclass(frozen=True)
class MemoryExclusion:
    memory_id: str
    reason: str
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MemoryConflict:
    memory_ids: tuple[str, ...]
    reason: str
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["memory_ids"] = list(self.memory_ids)
        return data


@dataclass
class MemoryContext:
    """The assembled, injectable memory context handed to an agent."""

    query: MemoryQuery
    evidences: list[MemoryEvidence] = field(default_factory=list)
    exclusions: list[MemoryExclusion] = field(default_factory=list)
    conflicts: list[MemoryConflict] = field(default_factory=list)
    budget_limit: int | None = None
    tokens_used: int = 0
    privacy_mode: bool = False
    created_at: str = field(default_factory=lambda: utc_now().isoformat(timespec="seconds"))

    @property
    def sources(self) -> list[str]:
        seen: list[str] = []
        for ev in self.evidences:
            if ev.source not in seen:
                seen.append(ev.source)
        return seen

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query.to_dict(),
            "privacy_mode": self.privacy_mode,
            "evidences": [e.to_dict() for e in self.evidences],
            "sources": self.sources,
            "exclusions": [x.to_dict() for x in self.exclusions],
            "conflicts": [c.to_dict() for c in self.conflicts],
            "budget": {
                "limit": self.budget_limit,
                "used": self.tokens_used,
                "remaining": (self.budget_limit - self.tokens_used) if self.budget_limit is not None else None,
            },
            "counts": {
                "injected": len(self.evidences),
                "excluded": len(self.exclusions),
                "conflicts": len(self.conflicts),
            },
            "created_at": self.created_at,
        }
