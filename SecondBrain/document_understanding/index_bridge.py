"""P1.3.7 - Bridge successful document ingestion into incremental RAG indexing.

P1.3.6 turns parser output into a stable ingestion result. This module closes
 the next pipeline gap: accepted ingestion results are converted into RAG document
 snapshots and applied through the existing incremental reindex service. Rejected
 or failed imports are explicitly skipped so bad parser output cannot pollute the
 vector index.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Iterable, Protocol, runtime_checkable

from .ingestion_pipeline import IngestionPipelineResult, IngestionPipelineStatus
from secondbrain.rag.indexing.change_detector import ChangeAction, DocumentSnapshot, hash_document_text
from secondbrain.rag.indexing.reindex_service import IndexRepository, ReindexPlan, ReindexService


class IngestionIndexStatus(str, Enum):
    """Stable index states for documents coming from the ingestion pipeline."""

    INDEXED = "indexed"
    SKIPPED = "skipped"
    DELETED = "deleted"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class IngestionIndexDocument:
    """Normalized document handed from ingestion to RAG indexing."""

    document_id: str
    title: str
    content: str
    content_hash: str
    source_path: str
    mime_type: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def snapshot(self) -> DocumentSnapshot:
        return DocumentSnapshot(
            document_id=self.document_id,
            content_hash=self.content_hash,
            metadata={
                "title": self.title,
                "source_path": self.source_path,
                "mime_type": self.mime_type,
                **dict(self.metadata),
            },
        )


@dataclass(frozen=True, slots=True)
class IngestionIndexResult:
    """Result of one ingestion-to-index transition."""

    document_id: str
    status: IngestionIndexStatus
    action: ChangeAction | None = None
    reason: str = ""
    message: str = ""

    @property
    def ok(self) -> bool:
        return self.status != IngestionIndexStatus.FAILED

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
class IngestionIndexSink(Protocol):
    """Boundary for real chunk/vector index side effects."""

    def index(self, document: IngestionIndexDocument) -> None:
        ...

    def delete(self, document_id: str) -> None:
        ...


@dataclass
class InMemoryIngestionIndexSink:
    """Deterministic sink for tests, dry-runs, and offline local mode."""

    indexed: dict[str, IngestionIndexDocument] = field(default_factory=dict)
    deleted: list[str] = field(default_factory=list)
    fail_on_index: set[str] = field(default_factory=set)
    fail_on_delete: set[str] = field(default_factory=set)

    def index(self, document: IngestionIndexDocument) -> None:
        if document.document_id in self.fail_on_index:
            raise RuntimeError(f"index rejected for {document.document_id}")
        self.indexed[document.document_id] = document

    def delete(self, document_id: str) -> None:
        if document_id in self.fail_on_delete:
            raise RuntimeError(f"delete rejected for {document_id}")
        self.indexed.pop(document_id, None)
        self.deleted.append(document_id)


DocumentFilter = Callable[[IngestionIndexDocument], bool]


class IngestionIndexBridge:
    """Apply successful ingestion results to the incremental RAG index.

    Rules:
    - only ``INGESTED`` and ``INGESTED_WITH_REVIEW`` become index candidates
    - rejected/failed ingestion results are skipped before reindex planning
    - document_id prefers runtime-returned ids, then parsed metadata, then path
    - unchanged content produces a SKIP plan without index side effects
    - sink failures are isolated unless ``fail_fast`` is enabled
    """

    def __init__(
        self,
        repository: IndexRepository,
        sink: IngestionIndexSink,
        *,
        document_filter: DocumentFilter | None = None,
        fail_fast: bool = False,
    ) -> None:
        self.repository = repository
        self.sink = sink
        self.document_filter = document_filter or (lambda _document: True)
        self.fail_fast = bool(fail_fast)
        self.results: list[IngestionIndexResult] = []
        self.last_plan: ReindexPlan | None = None

    def build_document(self, result: IngestionPipelineResult) -> IngestionIndexDocument:
        parsed = result.orchestration.parsed
        document_id = _resolve_document_id(result)
        content_hash = str(
            result.ingestion_result.get("content_hash")
            or parsed.metadata.get("content_hash")
            or hash_document_text(parsed.text)
        )
        return IngestionIndexDocument(
            document_id=document_id,
            title=parsed.title,
            content=parsed.text,
            content_hash=content_hash,
            source_path=parsed.source_path or result.path,
            mime_type=parsed.mime_type,
            metadata={
                "ingestion_status": result.status.value,
                "quality_decision": result.quality.decision.value,
                "parser_status": result.orchestration.parsed.status.value,
                "parser_name": result.orchestration.selection.parser_name,
                "pipeline_path": result.path,
                **dict(parsed.metadata),
            },
        )

    def apply_results(self, ingestion_results: Iterable[IngestionPipelineResult]) -> ReindexPlan:
        documents: list[IngestionIndexDocument] = []
        for ingestion_result in ingestion_results:
            candidate_id = _resolve_document_id(ingestion_result)
            if ingestion_result.status not in {
                IngestionPipelineStatus.INGESTED,
                IngestionPipelineStatus.INGESTED_WITH_REVIEW,
            }:
                self.results.append(
                    IngestionIndexResult(
                        document_id=candidate_id,
                        status=IngestionIndexStatus.SKIPPED,
                        reason="ingestion_not_successful",
                        message=f"ingestion status={ingestion_result.status.value}",
                    )
                )
                continue
            document = self.build_document(ingestion_result)
            if not self.document_filter(document):
                self.results.append(
                    IngestionIndexResult(
                        document_id=document.document_id,
                        status=IngestionIndexStatus.SKIPPED,
                        reason="filtered",
                    )
                )
                continue
            documents.append(document)

        by_id = {document.document_id: document for document in documents}

        def on_reindex(snapshot: DocumentSnapshot) -> None:
            self.sink.index(by_id[snapshot.document_id])

        service = ReindexService(self.repository, on_reindex=on_reindex)
        try:
            plan = service.apply(document.snapshot() for document in documents)
        except Exception as exc:  # noqa: BLE001 - bridge converts side-effect failures into release-gate data
            if self.fail_fast:
                raise
            failed_id = _extract_failed_document_id(str(exc), by_id.keys()) or "unknown"
            self.results.append(
                IngestionIndexResult(
                    document_id=failed_id,
                    status=IngestionIndexStatus.FAILED,
                    reason="index_failure",
                    message=str(exc),
                )
            )
            plan = service.plan(document.snapshot() for document in documents)

        self.last_plan = plan
        self._append_plan_results(plan)
        return plan

    def apply_deleted(self, document_ids: Iterable[str]) -> list[IngestionIndexResult]:
        emitted: list[IngestionIndexResult] = []
        for document_id in sorted(set(map(str, document_ids))):
            try:
                self.repository.delete_document(document_id)
                self.sink.delete(document_id)
                result = IngestionIndexResult(
                    document_id=document_id,
                    status=IngestionIndexStatus.DELETED,
                    action=ChangeAction.DELETE,
                    reason="document_deleted",
                )
            except Exception as exc:  # noqa: BLE001 - per-document delete failure isolation
                if self.fail_fast:
                    raise
                result = IngestionIndexResult(
                    document_id=document_id,
                    status=IngestionIndexStatus.FAILED,
                    action=ChangeAction.DELETE,
                    reason="delete_failure",
                    message=str(exc),
                )
            self.results.append(result)
            emitted.append(result)
        return emitted

    def snapshot(self) -> dict[str, Any]:
        indexed = sum(1 for result in self.results if result.status == IngestionIndexStatus.INDEXED)
        skipped = sum(1 for result in self.results if result.status == IngestionIndexStatus.SKIPPED)
        deleted = sum(1 for result in self.results if result.status == IngestionIndexStatus.DELETED)
        failed = sum(1 for result in self.results if result.status == IngestionIndexStatus.FAILED)
        plan_summary = self.last_plan.summary() if self.last_plan is not None else {
            "total": 0,
            "reindex": 0,
            "delete": 0,
            "skip": 0,
        }
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
                status = IngestionIndexStatus.INDEXED
            elif change.action == ChangeAction.DELETE:
                status = IngestionIndexStatus.DELETED
            else:
                status = IngestionIndexStatus.SKIPPED
            key = (change.document_id, change.reason)
            if key in existing:
                continue
            self.results.append(
                IngestionIndexResult(
                    document_id=change.document_id,
                    status=status,
                    action=change.action,
                    reason=change.reason,
                )
            )


def _resolve_document_id(result: IngestionPipelineResult) -> str:
    parsed = result.orchestration.parsed
    raw = (
        result.ingestion_result.get("document_id")
        or result.ingestion_result.get("id")
        or parsed.metadata.get("document_id")
        or parsed.metadata.get("id")
        or parsed.source_path
        or result.path
    )
    return str(raw)


def _extract_failed_document_id(message: str, document_ids: Iterable[str]) -> str | None:
    for document_id in document_ids:
        if document_id in message:
            return document_id
    return None
