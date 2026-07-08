"""Bulk workflow event names and event sink."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

BULK_JOB_CREATED = "BULK_JOB_CREATED"
BULK_JOB_STARTED = "BULK_JOB_STARTED"
BULK_PROGRESS_UPDATED = "BULK_PROGRESS_UPDATED"
BULK_ITEM_FAILED = "BULK_ITEM_FAILED"
BULK_JOB_COMPLETED = "BULK_JOB_COMPLETED"
BULK_JOB_CANCELLED = "BULK_JOB_CANCELLED"
BULK_ROLLBACK_STARTED = "BULK_ROLLBACK_STARTED"
BULK_ROLLBACK_COMPLETED = "BULK_ROLLBACK_COMPLETED"


@dataclass(frozen=True)
class BulkEvent:
    event_type: str
    job_id: str
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class BulkEventSink:
    def __init__(self) -> None:
        self.events: list[BulkEvent] = []

    def emit(self, event_type: str, job_id: str, **payload: Any) -> BulkEvent:
        event = BulkEvent(event_type=event_type, job_id=job_id, payload=dict(payload))
        self.events.append(event)
        return event
