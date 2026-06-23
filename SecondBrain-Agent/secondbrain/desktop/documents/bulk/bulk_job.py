"""Bulk document job model."""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from .bulk_state import BulkJobState, TERMINAL_STATES


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class BulkItemResult:
    document_id: str
    success: bool
    error: str | None = None


@dataclass(frozen=True)
class BulkJob:
    action: str
    document_ids: tuple[str, ...]
    job_id: str = field(default_factory=lambda: f"bulk_{uuid4().hex}")
    state: BulkJobState = BulkJobState.CREATED
    processed_items: int = 0
    failed_items: int = 0
    started_at: datetime | None = None
    finished_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    item_results: tuple[BulkItemResult, ...] = field(default_factory=tuple)

    @property
    def total_items(self) -> int:
        return len(self.document_ids)

    @property
    def progress_percent(self) -> int:
        if self.total_items == 0:
            return 100 if self.state in TERMINAL_STATES else 0
        return int((self.processed_items / self.total_items) * 100)

    @property
    def can_rollback(self) -> bool:
        return bool(self.metadata.get("rollback")) and self.state in {BulkJobState.COMPLETED, BulkJobState.PARTIAL_FAILURE}

    def transition(self, state: BulkJobState, **changes: Any) -> "BulkJob":
        if not isinstance(state, BulkJobState):
            state = BulkJobState(state)
        values: dict[str, Any] = {"state": state, **changes}
        if state == BulkJobState.RUNNING and self.started_at is None:
            values.setdefault("started_at", utc_now())
        if state in TERMINAL_STATES and self.finished_at is None:
            values.setdefault("finished_at", utc_now())
        return replace(self, **values)

    def with_result(self, result: BulkItemResult) -> "BulkJob":
        return replace(
            self,
            processed_items=self.processed_items + 1,
            failed_items=self.failed_items + (0 if result.success else 1),
            item_results=self.item_results + (result,),
        )

    def with_metadata(self, **metadata: Any) -> "BulkJob":
        merged = dict(self.metadata)
        merged.update(metadata)
        return replace(self, metadata=merged)
