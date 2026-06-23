from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import StrEnum
from hashlib import sha256
from typing import Any
from uuid import uuid4


class MemoryScope(StrEnum):
    SESSION = "session"
    WORKSPACE = "workspace"
    USER = "user"


class MemoryVisibility(StrEnum):
    PRIVATE = "private"
    WORKSPACE = "workspace"
    PUBLIC = "public"


class MemoryError(ValueError):
    pass


@dataclass(frozen=True)
class MemoryRecord:
    memory_id: str
    text: str
    scope: MemoryScope = MemoryScope.SESSION
    visibility: MemoryVisibility = MemoryVisibility.PRIVATE
    workspace_id: str | None = None
    tags: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def fingerprint(self) -> str:
        raw = "|".join([self.scope.value, self.workspace_id or "", self.text.strip().lower()])
        return sha256(raw.encode("utf-8")).hexdigest()


def create_memory_record(
    text: str,
    *,
    scope: MemoryScope = MemoryScope.SESSION,
    visibility: MemoryVisibility = MemoryVisibility.PRIVATE,
    workspace_id: str | None = None,
    tags: list[str] | tuple[str, ...] | None = None,
    metadata: dict[str, Any] | None = None,
) -> MemoryRecord:
    normalized = (text or "").strip()
    if not normalized:
        raise MemoryError("memory_text_required")
    if scope == MemoryScope.WORKSPACE and not workspace_id:
        raise MemoryError("workspace_id_required")
    return MemoryRecord(
        memory_id=str(uuid4()),
        text=normalized,
        scope=scope,
        visibility=visibility,
        workspace_id=workspace_id,
        tags=tuple(tags or ()),
        metadata=metadata or {},
    )


class InMemoryMemoryStore:
    def __init__(self) -> None:
        self._records: dict[str, MemoryRecord] = {}
        self._fingerprints: set[str] = set()

    def add(self, record: MemoryRecord) -> MemoryRecord:
        if record.fingerprint in self._fingerprints:
            raise MemoryError("duplicate_memory")
        self._records[record.memory_id] = record
        self._fingerprints.add(record.fingerprint)
        return record

    def list(self, *, workspace_id: str | None = None, scope: MemoryScope | None = None) -> list[MemoryRecord]:
        records = list(self._records.values())
        if workspace_id is not None:
            records = [record for record in records if record.workspace_id == workspace_id]
        if scope is not None:
            records = [record for record in records if record.scope == scope]
        return sorted(records, key=lambda record: record.created_at)

    def search(self, query: str, *, workspace_id: str | None = None, limit: int = 10) -> list[MemoryRecord]:
        normalized = (query or "").strip().lower()
        if not normalized:
            return []
        matches = [record for record in self.list(workspace_id=workspace_id) if normalized in record.text.lower()]
        return matches[: max(0, limit)]
