"""P1.2.7 - Bridge connector import jobs into incremental RAG indexing.

Connector P1.2.6 creates stable ``ConnectorImportJob`` objects at the
 ingestion boundary. This module converts accepted jobs into RAG document
 snapshots and applies the existing incremental reindex planner. The bridge
 keeps connector sync, ingestion, and RAG indexing loosely coupled while making
 the end-to-end state transition observable and deterministic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Iterable, Protocol, runtime_checkable

from .import_bridge import ConnectorImportJob, ImportJobStatus
from secondbrain.rag.indexing.change_detector import ChangeAction, DocumentSnapshot
from secondbrain.rag.indexing.reindex_service import IndexRepository, ReindexPlan, ReindexService


class ConnectorIndexStatus(str, Enum):
    """Stable index statuses for connector-originated documents."""

    INDEXED = "indexed"
    SKIPPED = "skipped"
    DELETED = "deleted"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class ConnectorIndexDocument:
    """Normalized RAG document produced from a connector import job."""

    document_id: str
    title: str
    content: str
    content_hash: str
    source: str
    external_id: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def snapshot(self) -> DocumentSnapshot:
        return DocumentSnapshot(
            document_id=self.document_id,
            content_hash=self.content_hash,
            metadata={
                "title": self.title,
                "source": self.source,
                "external_id": self.external_id,
                **dict(self.metadata),
            },
        )


@dataclass(frozen=True, slots=True)
class ConnectorIndexResult:
    """Result of a single connector document index decision."""

    document_id: str
    status: ConnectorIndexStatus
    action: ChangeAction | None = None
    reason: str = ""
    message: str = ""

    @property
    def ok(self) -> bool:
        return self.status != ConnectorIndexStatus.FAILED

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "status": self.status.value,
            "action": self.action.value if self.action is not None else None,
            "reason": self.reason,
            "message": self.message,
            "ok": self.ok,
        }


@runtime_checkable
class IndexDocumentSink(Protocol):
    """Boundary for actual vector/chunk indexing side effects."""

    def index(self, document: ConnectorIndexDocument) -> None:
        ...

    def delete(self, document_id: str) -> None:
        ...


@dataclass
class InMemoryIndexDocumentSink:
    """Deterministic sink for tests, local dry-runs, and no-vector mode."""

    indexed: dict[str, ConnectorIndexDocument] = field(default_factory=dict)
    deleted: list[str] = field(default_factory=list)
    fail_on_index: set[str] = field(default_factory=set)
    fail_on_delete: set[str] = field(default_factory=set)

    def index(self, document: ConnectorIndexDocument) -> None:
        if document.document_id in self.fail_on_index:
            raise RuntimeError(f"index rejected for {document.document_id}")
        self.indexed[document.document_id] = document

    def delete(self, document_id: str) -> None:
        if document_id in self.fail_on_delete:
            raise RuntimeError(f"delete rejected for {document_id}")
        self.indexed.pop(document_id, None)
        self.deleted.append(document_id)


DocumentFilter = Callable[[ConnectorIndexDocument], bool]


class ConnectorIndexBridge:
    """Apply connector import jobs to the incremental RAG index plan.

    Rules:
    - only IMPORTED jobs are index candidates by default
    - document_id uses ``document_key`` so content changes replace vectors for
      the same external source document instead of creating duplicates
    - content_hash drives skip/reindex decisions
    - failures are isolated into result entries and re-raised only when
      ``fail_fast`` is enabled
    """

    def __init__(
        self,
        repository: IndexRepository,
        sink: IndexDocumentSink,
        *,
        document_filter: DocumentFilter | None = None,
        fail_fast: bool = False,
    ) -> None:
        self.repository = repository
        self.sink = sink
        self.document_filter = document_filter or (lambda _document: True)
        self.fail_fast = bool(fail_fast)
        self.results: list[ConnectorIndexResult] = []
        self.last_plan: ReindexPlan | None = None

    def build_document(self, job: ConnectorImportJob) -> ConnectorIndexDocument:
        return ConnectorIndexDocument(
            document_id=job.document_key,
            title=job.title,
            content=job.content,
            content_hash=job.content_hash,
            source=job.source,
            external_id=job.external_id,
            metadata={
                "connector_job_id": job.job_id,
                "connector_uri": job.uri,
                "connector_mime_type": job.mime_type,
                "connector_updated_at": job.updated_at.isoformat(),
                **dict(job.metadata),
            },
        )

    def apply_jobs(self, jobs: Iterable[ConnectorImportJob]) -> ReindexPlan:
        documents: list[ConnectorIndexDocument] = []
        for job in jobs:
            if job.status != ImportJobStatus.IMPORTED:
                self.results.append(
                    ConnectorIndexResult(
                        document_id=job.document_key,
                        status=ConnectorIndexStatus.SKIPPED,
                        reason="job_not_imported",
                        message=f"import status={job.status.value}",
                    )
                )
                continue
            document = self.build_document(job)
            if not self.document_filter(document):
                self.results.append(
                    ConnectorIndexResult(
                        document_id=document.document_id,
                        status=ConnectorIndexStatus.SKIPPED,
                        reason="filtered",
                    )
                )
                continue
            documents.append(document)

        by_id = {document.document_id: document for document in documents}

        def on_reindex(snapshot: DocumentSnapshot) -> None:
            document = by_id[snapshot.document_id]
            self.sink.index(document)

        service = ReindexService(self.repository, on_reindex=on_reindex)
        try:
            plan = service.apply(document.snapshot() for document in documents)
        except Exception as exc:  # noqa: BLE001 - bridge converts index-side failures into release-gate data
            if self.fail_fast:
                raise
            failed_id = _extract_failed_document_id(str(exc), by_id.keys())
            self.results.append(
                ConnectorIndexResult(
                    document_id=failed_id or "unknown",
                    status=ConnectorIndexStatus.FAILED,
                    reason="index_failure",
                    message=str(exc),
                )
            )
            plan = service.plan(document.snapshot() for document in documents)

        self.last_plan = plan
        self._append_plan_results(plan)
        return plan

    def apply_deleted(self, document_ids: Iterable[str]) -> list[ConnectorIndexResult]:
        emitted: list[ConnectorIndexResult] = []
        for document_id in sorted(set(map(str, document_ids))):
            try:
                self.repository.delete_document(document_id)
                self.sink.delete(document_id)
                result = ConnectorIndexResult(
                    document_id=document_id,
                    status=ConnectorIndexStatus.DELETED,
                    action=ChangeAction.DELETE,
                    reason="connector_deleted",
                )
            except Exception as exc:  # noqa: BLE001 - delete failures must remain isolated per document
                if self.fail_fast:
                    raise
                result = ConnectorIndexResult(
                    document_id=document_id,
                    status=ConnectorIndexStatus.FAILED,
                    action=ChangeAction.DELETE,
                    reason="delete_failure",
                    message=str(exc),
                )
            self.results.append(result)
            emitted.append(result)
        return emitted

    def snapshot(self) -> dict[str, Any]:
        indexed = sum(1 for result in self.results if result.status == ConnectorIndexStatus.INDEXED)
        skipped = sum(1 for result in self.results if result.status == ConnectorIndexStatus.SKIPPED)
        deleted = sum(1 for result in self.results if result.status == ConnectorIndexStatus.DELETED)
        failed = sum(1 for result in self.results if result.status == ConnectorIndexStatus.FAILED)
        plan_summary = self.last_plan.summary() if self.last_plan is not None else {"total": 0, "reindex": 0, "delete": 0, "skip": 0}
        return {
            "total": len(self.results),
            "indexed": indexed,
            "skipped": skipped,
            "deleted": deleted,
            "failed": failed,
            "ok": failed == 0,
            "plan": plan_summary,
            "results": [result.to_dict() for result in self.results],
        }

    def _append_plan_results(self, plan: ReindexPlan) -> None:
        existing = {(result.document_id, result.reason) for result in self.results}
        for change in plan.changes:
            if change.action == ChangeAction.REINDEX:
                status = ConnectorIndexStatus.INDEXED
            elif change.action == ChangeAction.DELETE:
                status = ConnectorIndexStatus.DELETED
            else:
                status = ConnectorIndexStatus.SKIPPED
            key = (change.document_id, change.reason)
            if key in existing:
                continue
            self.results.append(
                ConnectorIndexResult(
                    document_id=change.document_id,
                    status=status,
                    action=change.action,
                    reason=change.reason,
                )
            )


def _extract_failed_document_id(message: str, document_ids: Iterable[str]) -> str | None:
    for document_id in document_ids:
        if document_id in message:
            return document_id
    return None
