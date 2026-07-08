"""Incremental reindex orchestration for RAG document vectors."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable, Protocol

from .change_detector import ChangeAction, ChangeDetector, DocumentSnapshot, PlannedChange


class IndexRepository(Protocol):
    def list_snapshots(self) -> list[DocumentSnapshot]:
        ...

    def upsert_document(self, snapshot: DocumentSnapshot) -> None:
        ...

    def delete_document(self, document_id: str) -> None:
        ...


@dataclass(frozen=True)
class ReindexPlan:
    changes: list[PlannedChange]

    @property
    def to_reindex(self) -> list[PlannedChange]:
        return [change for change in self.changes if change.action == ChangeAction.REINDEX]

    @property
    def to_delete(self) -> list[PlannedChange]:
        return [change for change in self.changes if change.action == ChangeAction.DELETE]

    @property
    def skipped(self) -> list[PlannedChange]:
        return [change for change in self.changes if change.action == ChangeAction.SKIP]

    def summary(self) -> dict[str, int]:
        return {
            "total": len(self.changes),
            "reindex": len(self.to_reindex),
            "delete": len(self.to_delete),
            "skip": len(self.skipped),
        }


@dataclass
class InMemoryIndexRepository:
    """Deterministic local repository for tests and offline execution."""

    snapshots: dict[str, DocumentSnapshot] = field(default_factory=dict)
    deleted_document_ids: list[str] = field(default_factory=list)
    upserted_document_ids: list[str] = field(default_factory=list)

    def list_snapshots(self) -> list[DocumentSnapshot]:
        return [self.snapshots[key] for key in sorted(self.snapshots)]

    def upsert_document(self, snapshot: DocumentSnapshot) -> None:
        self.snapshots[snapshot.document_id] = snapshot
        self.upserted_document_ids.append(snapshot.document_id)

    def delete_document(self, document_id: str) -> None:
        self.snapshots.pop(document_id, None)
        self.deleted_document_ids.append(document_id)


class ReindexService:
    """Builds and applies incremental RAG index updates."""

    def __init__(
        self,
        repository: IndexRepository,
        *,
        detector: ChangeDetector | None = None,
        on_reindex: Callable[[DocumentSnapshot], None] | None = None,
    ) -> None:
        self.repository = repository
        self.detector = detector or ChangeDetector()
        self.on_reindex = on_reindex

    def plan(self, current_snapshots: Iterable[DocumentSnapshot]) -> ReindexPlan:
        changes = self.detector.plan(self.repository.list_snapshots(), list(current_snapshots))
        return ReindexPlan(changes=changes)

    def apply(self, current_snapshots: Iterable[DocumentSnapshot]) -> ReindexPlan:
        current_by_id = {snapshot.document_id: snapshot for snapshot in current_snapshots}
        plan = self.plan(current_by_id.values())

        for change in plan.changes:
            if change.action == ChangeAction.REINDEX:
                snapshot = current_by_id[change.document_id]
                if self.on_reindex is not None:
                    self.on_reindex(snapshot)
                self.repository.upsert_document(snapshot)
            elif change.action == ChangeAction.DELETE:
                self.repository.delete_document(change.document_id)

        return plan
