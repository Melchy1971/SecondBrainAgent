"""Document center domain models."""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class DocumentStatus(str, Enum):
    NEW = "NEW"
    IMPORTED = "IMPORTED"
    INDEXING = "INDEXING"
    INDEXED = "INDEXED"
    FAILED = "FAILED"
    ARCHIVED = "ARCHIVED"


@dataclass(frozen=True)
class DesktopDocument:
    document_id: str
    title: str
    workspace_id: str
    source: str
    status: DocumentStatus = DocumentStatus.NEW
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    tags: tuple[str, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)

    def with_update(self, **changes: Any) -> "DesktopDocument":
        changes.setdefault("updated_at", utc_now())
        if "status" in changes and not isinstance(changes["status"], DocumentStatus):
            changes["status"] = DocumentStatus(changes["status"])
        if "tags" in changes:
            changes["tags"] = tuple(dict.fromkeys(str(t).strip() for t in changes["tags"] if str(t).strip()))
        return replace(self, **changes)

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "title": self.title,
            "workspace_id": self.workspace_id,
            "source": self.source,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "tags": list(self.tags),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DesktopDocument":
        return cls(
            document_id=str(data["document_id"]),
            title=str(data.get("title") or data["document_id"]),
            workspace_id=str(data["workspace_id"]),
            source=str(data.get("source", "unknown")),
            status=DocumentStatus(data.get("status", DocumentStatus.NEW.value)),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else utc_now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else utc_now(),
            tags=tuple(data.get("tags", ())),
            metadata=dict(data.get("metadata", {})),
        )
