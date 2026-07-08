"""High-level bulk workflow orchestration."""
from __future__ import annotations

from typing import Any

from ..document_repository import DocumentRepository
from .bulk_events import BULK_JOB_COMPLETED, BULK_JOB_CREATED, BULK_JOB_STARTED, BulkEventSink
from .bulk_executor import BulkExecutor
from .bulk_history import BulkHistory
from .bulk_job import BulkJob
from .bulk_queue import BulkQueue
from .bulk_state import BulkJobState
from .rollback_manager import RollbackManager


class BulkValidationError(ValueError):
    pass


class BulkEngine:
    def __init__(
        self,
        repository: DocumentRepository,
        *,
        queue: BulkQueue | None = None,
        history: BulkHistory | None = None,
        events: BulkEventSink | None = None,
        rollback_manager: RollbackManager | None = None,
    ) -> None:
        self.repository = repository
        self.queue = queue or BulkQueue()
        self.history = history or BulkHistory()
        self.events = events or BulkEventSink()
        self.rollback_manager = rollback_manager or RollbackManager()
        self.executor = BulkExecutor(repository, self.events)

    def create_job(self, action: str, document_ids: list[str] | tuple[str, ...], **metadata: Any) -> BulkJob:
        clean_ids = tuple(dict.fromkeys(str(document_id).strip() for document_id in document_ids if str(document_id).strip()))
        if not action or not action.strip():
            raise BulkValidationError("action is required")
        if not clean_ids:
            raise BulkValidationError("at least one document_id is required")
        rollback = self.rollback_manager.capture_snapshot(self.repository, clean_ids)
        job = BulkJob(action=action.strip(), document_ids=clean_ids).with_metadata(**metadata, rollback=rollback)
        self.history.record(job)
        self.events.emit(BULK_JOB_CREATED, job.job_id, action=job.action, total=job.total_items)
        return job

    def enqueue(self, job: BulkJob) -> BulkJob:
        queued = self.queue.enqueue(job.transition(BulkJobState.VALIDATED))
        self.history.record(queued)
        return queued

    def run_next(self) -> BulkJob | None:
        job = self.queue.dequeue()
        if job is None:
            return None
        self.events.emit(BULK_JOB_STARTED, job.job_id)
        completed = self.executor.execute(job)
        self.history.record(completed)
        self.events.emit(
            BULK_JOB_COMPLETED,
            completed.job_id,
            state=completed.state.value,
            processed=completed.processed_items,
            failed=completed.failed_items,
        )
        return completed

    def run_immediately(self, action: str, document_ids: list[str] | tuple[str, ...], **metadata: Any) -> BulkJob:
        return self.executor.execute(self.create_job(action, document_ids, **metadata))

    def rollback(self, job_id: str) -> BulkJob:
        job = self.history.get(job_id)
        if job is None:
            raise KeyError(f"bulk job not found: {job_id}")
        restored = self.rollback_manager.rollback(self.repository, job, self.events)
        self.history.record(restored)
        return restored
