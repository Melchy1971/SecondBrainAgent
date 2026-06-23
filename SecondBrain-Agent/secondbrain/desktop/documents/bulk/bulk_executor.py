"""Bulk document action executor."""
from __future__ import annotations

from typing import Any, Callable

from ..document_repository import DocumentRepository
from ..models import DocumentStatus
from .bulk_events import BULK_ITEM_FAILED, BULK_PROGRESS_UPDATED, BulkEventSink
from .bulk_job import BulkItemResult, BulkJob
from .bulk_state import BulkJobState


class UnsupportedBulkActionError(ValueError):
    pass


class BulkExecutor:
    def __init__(self, repository: DocumentRepository, events: BulkEventSink | None = None) -> None:
        self.repository = repository
        self.events = events or BulkEventSink()
        self._handlers: dict[str, Callable[[str, dict[str, Any]], None]] = {
            "archive": self._archive,
            "delete": self._delete,
            "reindex": self._reindex,
            "move_workspace": self._move_workspace,
            "add_tags": self._add_tags,
            "remove_tags": self._remove_tags,
            "export_metadata": self._export_metadata,
        }

    def execute(self, job: BulkJob) -> BulkJob:
        action = job.action.lower().strip()
        handler = self._handlers.get(action)
        if handler is None:
            raise UnsupportedBulkActionError(f"unsupported bulk action: {job.action}")

        running = job.transition(BulkJobState.RUNNING)
        for document_id in job.document_ids:
            try:
                handler(document_id, running.metadata)
                result = BulkItemResult(document_id=document_id, success=True)
            except Exception as exc:  # deterministic item-level isolation
                result = BulkItemResult(document_id=document_id, success=False, error=str(exc))
                self.events.emit(BULK_ITEM_FAILED, running.job_id, document_id=document_id, error=str(exc))
            running = running.with_result(result)
            self.events.emit(
                BULK_PROGRESS_UPDATED,
                running.job_id,
                processed=running.processed_items,
                total=running.total_items,
                failed=running.failed_items,
            )

        final_state = BulkJobState.COMPLETED if running.failed_items == 0 else BulkJobState.PARTIAL_FAILURE
        return running.transition(final_state)

    def _require(self, document_id: str):
        return self.repository.require(document_id)

    def _archive(self, document_id: str, metadata: dict[str, Any]) -> None:
        document = self._require(document_id)
        self.repository.save(document.with_update(status=DocumentStatus.ARCHIVED))

    def _delete(self, document_id: str, metadata: dict[str, Any]) -> None:
        if not self.repository.delete(document_id):
            raise KeyError(f"document not found: {document_id}")

    def _reindex(self, document_id: str, metadata: dict[str, Any]) -> None:
        document = self._require(document_id)
        self.repository.save(document.with_update(status=DocumentStatus.INDEXING))

    def _move_workspace(self, document_id: str, metadata: dict[str, Any]) -> None:
        target_workspace = str(metadata.get("target_workspace_id") or "").strip()
        if not target_workspace:
            raise ValueError("target_workspace_id is required")
        document = self._require(document_id)
        self.repository.save(document.with_update(workspace_id=target_workspace))

    def _add_tags(self, document_id: str, metadata: dict[str, Any]) -> None:
        tags = tuple(str(tag).strip() for tag in metadata.get("tags", ()) if str(tag).strip())
        document = self._require(document_id)
        self.repository.save(document.with_update(tags=document.tags + tags))

    def _remove_tags(self, document_id: str, metadata: dict[str, Any]) -> None:
        remove = {str(tag).strip() for tag in metadata.get("tags", ())}
        document = self._require(document_id)
        self.repository.save(document.with_update(tags=tuple(tag for tag in document.tags if tag not in remove)))

    def _export_metadata(self, document_id: str, metadata: dict[str, Any]) -> None:
        self._require(document_id)
