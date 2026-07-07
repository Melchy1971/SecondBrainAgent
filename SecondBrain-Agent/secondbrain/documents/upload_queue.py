"""Multi-import upload queue with per-item progress + status."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class UploadStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


@dataclass
class UploadItem:
    id: str
    path: str
    size: int = 0
    status: UploadStatus = UploadStatus.PENDING
    progress: float = 0.0
    error: str | None = None
    doc_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "path": self.path, "size": self.size,
                "status": self.status.value, "progress": round(self.progress, 4),
                "error": self.error, "doc_id": self.doc_id}


class UploadQueue:
    def __init__(self) -> None:
        self._items: list[UploadItem] = []
        self._by_id: dict[str, UploadItem] = {}
        self._seq = 0

    def enqueue(self, path: str, size: int = 0) -> UploadItem:
        self._seq += 1
        item = UploadItem(id=f"u{self._seq}", path=path, size=size)
        self._items.append(item)
        self._by_id[item.id] = item
        return item

    def enqueue_many(self, paths: list[str]) -> list[UploadItem]:
        return [self.enqueue(p) for p in paths]

    def next_pending(self) -> UploadItem | None:
        return next((i for i in self._items if i.status is UploadStatus.PENDING), None)

    def mark_running(self, item_id: str) -> None:
        self._by_id[item_id].status = UploadStatus.RUNNING

    def set_progress(self, item_id: str, progress: float) -> None:
        self._by_id[item_id].progress = max(0.0, min(1.0, progress))

    def mark_done(self, item_id: str, *, doc_id: str | None = None) -> None:
        it = self._by_id[item_id]
        it.status = UploadStatus.DONE; it.progress = 1.0; it.doc_id = doc_id

    def mark_failed(self, item_id: str, error: str) -> None:
        it = self._by_id[item_id]
        it.status = UploadStatus.FAILED; it.error = error

    def items(self) -> list[UploadItem]:
        return list(self._items)

    def summary(self) -> dict[str, int]:
        out = {s.value: 0 for s in UploadStatus}
        for it in self._items:
            out[it.status.value] += 1
        out["total"] = len(self._items)
        return out
