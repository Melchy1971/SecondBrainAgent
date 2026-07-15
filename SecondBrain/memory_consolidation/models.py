"""Data model for long-term memory consolidation.

A memory is never silently mutated: corrections and merges create a new active
record and mark the old one ``superseded`` (retained), and every record keeps
its evidence and source ids for provenance. Decay lowers an effective
confidence over time but never removes an important or protected memory.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

__all__ = [
    "MemoryType", "MemoryStatus", "ConflictType", "Decision", "Memory",
    "MemoryConflict", "DuplicateGroup", "TYPE_HALFLIFE_DAYS",
]


class MemoryType(StrEnum):
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PREFERENCE = "preference"
    PROJECT = "project"
    CONTACT = "contact"
    TASK = "task"
    SYSTEM = "system"


class MemoryStatus(StrEnum):
    ACTIVE = "active"
    CANDIDATE = "candidate"
    CONTRADICTORY = "contradictory"
    OUTDATED = "outdated"
    AMBIGUOUS = "ambiguous"
    UNSUPPORTED = "unsupported"
    SUPERSEDED = "superseded"
    EXPIRED = "expired"
    BLOCKED = "blocked"       # no_memory / secret / privacy
    PENDING = "pending"


class ConflictType(StrEnum):
    CONTRADICTORY = "contradictory"
    OUTDATED = "outdated"
    AMBIGUOUS = "ambiguous"
    UNSUPPORTED = "unsupported"


class Decision(StrEnum):
    KEEP_BOTH = "keep_both"
    SUPERSEDE = "supersede"
    MERGE = "merge"
    REJECT = "reject"
    DEFER = "defer"
    REQUEST_USER_CONFIRMATION = "request_user_confirmation"


# Decay half-life per type (days). Confirmed preferences age slowly; episodic
# memories fade fastest. ``None`` == no time-based decay.
TYPE_HALFLIFE_DAYS: dict[str, float | None] = {
    MemoryType.EPISODIC.value: 14.0,
    MemoryType.SEMANTIC.value: 365.0,
    MemoryType.PREFERENCE.value: 540.0,
    MemoryType.PROJECT.value: 120.0,
    MemoryType.CONTACT.value: 365.0,
    MemoryType.TASK.value: 30.0,
    MemoryType.SYSTEM.value: None,
}


@dataclass
class Memory:
    memory_id: str
    workspace_id: str
    type: str
    content: str
    normalized_content: str = ""
    evidence: list[dict[str, Any]] = field(default_factory=list)
    source_ids: list[str] = field(default_factory=list)
    confidence: float = 0.75
    importance: float = 0.5
    created_at: str = ""
    updated_at: str = ""
    last_used_at: str = ""
    last_confirmed_at: str = ""
    expires_at: str | None = None
    superseded_by: str = ""
    status: str = MemoryStatus.ACTIVE.value
    sensitive: bool = False
    no_memory: bool = False
    user_confirmed: bool = False
    version: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "memory_id": self.memory_id, "workspace_id": self.workspace_id, "type": self.type,
            "content": self.content, "evidence": [dict(e) for e in self.evidence],
            "normalized_content": self.normalized_content,
            "source_ids": list(self.source_ids), "confidence": round(float(self.confidence), 3),
            "importance": round(float(self.importance), 3), "created_at": self.created_at,
            "last_confirmed_at": self.last_confirmed_at, "expires_at": self.expires_at,
            "superseded_by": self.superseded_by, "status": self.status, "sensitive": self.sensitive,
            "no_memory": self.no_memory, "user_confirmed": self.user_confirmed,
            "updated_at": self.updated_at, "last_used_at": self.last_used_at, "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Memory":
        return cls(**{k: data.get(k, cls.__dataclass_fields__[k].default) for k in cls.__dataclass_fields__
                      if k not in ("evidence", "source_ids")},
                   evidence=[dict(e) for e in data.get("evidence", [])],
                   source_ids=list(data.get("source_ids", [])))


@dataclass
class MemoryConflict:
    conflict_type: str
    memory_ids: list[str]
    detail: str = ""
    status: str = "open"
    decision: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"conflict_type": self.conflict_type, "memory_ids": list(self.memory_ids),
                "detail": self.detail, "status": self.status, "decision": self.decision}


@dataclass
class DuplicateGroup:
    key: str
    memory_ids: list[str]
    similarity: float

    def to_dict(self) -> dict[str, Any]:
        return {"key": self.key, "memory_ids": list(self.memory_ids), "similarity": round(self.similarity, 3)}
