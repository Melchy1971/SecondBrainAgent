"""Import-Historie: Sicht für GUI und CLI."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from secondbrain.import_pipeline.models import ImportStatus
from secondbrain.import_pipeline.store import ImportJobStore

SCHEMA = "secondbrain.import_pipeline.history.v1"


class ImportHistory:
    def __init__(self, project_root: str | Path = "."):
        self.store = ImportJobStore(project_root)

    def snapshot(self, *, status: str | None = None, limit: int = 200) -> dict[str, Any]:
        jobs = self.store.list(status=status, limit=limit)
        return {
            "schema": SCHEMA,
            "counts": self.store.counts(),
            "open": [s for s in (
                ImportStatus.QUEUED,
                ImportStatus.FAILED,
                ImportStatus.OCR_REQUIRED,
                ImportStatus.REVIEW_REQUIRED,
                ImportStatus.FAILED_REVIEWABLE,
                ImportStatus.REVIEW_DEFERRED,
            ) if self.store.counts().get(s)],
            "jobs": [
                {
                    "job_id": j.job_id,
                    "source_kind": j.source_kind,
                    "source_ref": j.source_ref,
                    "connector": j.connector,
                    "status": j.status,
                    "attempts": j.attempts,
                    "ocr_required": j.ocr_required,
                    "document_type": j.document_type,
                    "tags": j.tags,
                    "chunk_count": j.chunk_count,
                    "error": j.error,
                    "error_category": j.error_category,
                    "document_id": j.document_id,
                    "parser": j.parser,
                    "confidence": j.confidence,
                    "review_id": j.review_id,
                    "review_category": j.review_category,
                    "review_status": j.review_status,
                    "retry_allowed": j.retry_allowed,
                    "indexing_blocked": j.indexing_blocked,
                    "classification_blocked": j.classification_blocked,
                    "memory_forwarding_blocked": j.memory_forwarding_blocked,
                    "connector_forwarding_blocked": j.connector_forwarding_blocked,
                    "created_at": j.created_at,
                    "updated_at": j.updated_at,
                    "duplicate_of": j.duplicate_of,
                    "stage_history": j.stage_history,
                }
                for j in jobs
            ],
        }
