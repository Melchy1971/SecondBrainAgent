"""Rollback metadata builder and executor for document bulk operations."""
from __future__ import annotations

from typing import Any

from ..document_repository import DocumentRepository
from ..models import DesktopDocument
from .bulk_job import BulkJob
from .bulk_events import BULK_ROLLBACK_COMPLETED, BULK_ROLLBACK_STARTED, BulkEventSink
from .bulk_state import BulkJobState


class RollbackManager:
    def capture_snapshot(self, repository: DocumentRepository, document_ids: list[str] | tuple[str, ...]) -> dict[str, Any]:
        snapshots: dict[str, dict[str, Any]] = {}
        missing: list[str] = []
        for document_id in document_ids:
            document = repository.get(document_id)
            if document is None:
                missing.append(document_id)
            else:
                snapshots[document_id] = document.to_dict()
        return {"documents": snapshots, "missing": missing}

    def rollback(self, repository: DocumentRepository, job: BulkJob, events: BulkEventSink | None = None) -> BulkJob:
        rollback = job.metadata.get("rollback") or {}
        documents = rollback.get("documents") or {}
        if events:
            events.emit(BULK_ROLLBACK_STARTED, job.job_id)
        for payload in documents.values():
            repository.save(DesktopDocument.from_dict(payload))
        restored = job.transition(BulkJobState.ROLLBACK)
        if events:
            events.emit(BULK_ROLLBACK_COMPLETED, job.job_id, restored=len(documents))
        return restored
