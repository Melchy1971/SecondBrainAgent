"""Bulk workflow state model."""
from __future__ import annotations

from enum import Enum


class BulkJobState(str, Enum):
    CREATED = "CREATED"
    VALIDATED = "VALIDATED"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    PARTIAL_FAILURE = "PARTIAL_FAILURE"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    ROLLBACK = "ROLLBACK"


TERMINAL_STATES = {
    BulkJobState.COMPLETED,
    BulkJobState.PARTIAL_FAILURE,
    BulkJobState.FAILED,
    BulkJobState.CANCELLED,
}
