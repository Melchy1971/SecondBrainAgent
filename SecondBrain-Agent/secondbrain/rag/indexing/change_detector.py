"""Document-hash based change detection for incremental RAG reindexing."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable, Mapping


class ChangeAction(str, Enum):
    """Allowed reindex operations."""

    SKIP = "skip"
    REINDEX = "reindex"
    DELETE = "delete"


@dataclass(frozen=True)
class DocumentSnapshot:
    """Stable document state used to decide whether vectors need replacement."""

    document_id: str
    content_hash: str
    metadata: dict[str, object] = field(default_factory=dict)

    @classmethod
    def from_text(
        cls,
        document_id: str,
        text: str,
        *,
        metadata: Mapping[str, object] | None = None,
    ) -> "DocumentSnapshot":
        return cls(
            document_id=str(document_id),
            content_hash=hash_document_text(text),
            metadata=dict(metadata or {}),
        )


@dataclass(frozen=True)
class PlannedChange:
    """Single operation in an incremental reindex plan."""

    document_id: str
    action: ChangeAction
    old_hash: str | None = None
    new_hash: str | None = None
    reason: str = ""


class ChangeDetector:
    """Compares stored and current document snapshots.

    Rules:
    - missing old + present current => reindex
    - same hash => skip
    - changed hash => reindex
    - old missing from current set => delete
    """

    def plan(
        self,
        previous: Mapping[str, DocumentSnapshot] | Iterable[DocumentSnapshot],
        current: Mapping[str, DocumentSnapshot] | Iterable[DocumentSnapshot],
    ) -> list[PlannedChange]:
        previous_by_id = _as_snapshot_map(previous)
        current_by_id = _as_snapshot_map(current)

        changes: list[PlannedChange] = []
        all_ids = sorted(set(previous_by_id) | set(current_by_id))
        for document_id in all_ids:
            old = previous_by_id.get(document_id)
            new = current_by_id.get(document_id)
            if old is None and new is not None:
                changes.append(
                    PlannedChange(
                        document_id=document_id,
                        action=ChangeAction.REINDEX,
                        new_hash=new.content_hash,
                        reason="new_document",
                    )
                )
            elif old is not None and new is None:
                changes.append(
                    PlannedChange(
                        document_id=document_id,
                        action=ChangeAction.DELETE,
                        old_hash=old.content_hash,
                        reason="deleted_document",
                    )
                )
            elif old is not None and new is not None and old.content_hash != new.content_hash:
                changes.append(
                    PlannedChange(
                        document_id=document_id,
                        action=ChangeAction.REINDEX,
                        old_hash=old.content_hash,
                        new_hash=new.content_hash,
                        reason="content_changed",
                    )
                )
            elif old is not None and new is not None:
                changes.append(
                    PlannedChange(
                        document_id=document_id,
                        action=ChangeAction.SKIP,
                        old_hash=old.content_hash,
                        new_hash=new.content_hash,
                        reason="unchanged",
                    )
                )
        return changes


def hash_document_text(text: str) -> str:
    """Return stable hash for document content.

    Line endings are normalized. Leading/trailing whitespace is preserved because
    it can affect chunk boundaries and therefore vector payloads.
    """

    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _as_snapshot_map(
    snapshots: Mapping[str, DocumentSnapshot] | Iterable[DocumentSnapshot],
) -> dict[str, DocumentSnapshot]:
    if isinstance(snapshots, Mapping):
        return {str(key): value for key, value in snapshots.items()}
    return {snapshot.document_id: snapshot for snapshot in snapshots}
