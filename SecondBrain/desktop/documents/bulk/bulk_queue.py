"""FIFO queue for bulk document jobs."""
from __future__ import annotations

from collections import deque

from .bulk_job import BulkJob
from .bulk_state import BulkJobState


class BulkQueue:
    def __init__(self) -> None:
        self._items: deque[BulkJob] = deque()

    def enqueue(self, job: BulkJob) -> BulkJob:
        queued = job.transition(BulkJobState.QUEUED)
        self._items.append(queued)
        return queued

    def dequeue(self) -> BulkJob | None:
        if not self._items:
            return None
        return self._items.popleft()

    def list(self) -> list[BulkJob]:
        return list(self._items)

    def count(self) -> int:
        return len(self._items)

    def clear(self) -> None:
        self._items.clear()
