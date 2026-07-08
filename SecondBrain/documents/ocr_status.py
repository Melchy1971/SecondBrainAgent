"""Per-document OCR status tracking (ties to the vision OCR subsystem)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class OcrState(str, Enum):
    NONE = "none"
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


@dataclass
class OcrRecord:
    doc_id: str
    state: OcrState = OcrState.NONE
    pages: int = 0
    chars: int = 0
    mean_confidence: float = 0.0
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"doc_id": self.doc_id, "state": self.state.value, "pages": self.pages,
                "chars": self.chars, "mean_confidence": self.mean_confidence, "error": self.error}


class OcrStatusTracker:
    def __init__(self) -> None:
        self._records: dict[str, OcrRecord] = {}

    def _rec(self, doc_id: str) -> OcrRecord:
        return self._records.setdefault(doc_id, OcrRecord(doc_id=doc_id))

    def mark_pending(self, doc_id: str) -> None:
        self._rec(doc_id).state = OcrState.PENDING

    def mark_running(self, doc_id: str) -> None:
        self._rec(doc_id).state = OcrState.RUNNING

    def mark_done(self, doc_id: str, *, pages: int, chars: int, mean_confidence: float = 0.0) -> None:
        r = self._rec(doc_id)
        r.state = OcrState.DONE; r.pages = pages; r.chars = chars; r.mean_confidence = mean_confidence

    def mark_failed(self, doc_id: str, error: str) -> None:
        r = self._rec(doc_id); r.state = OcrState.FAILED; r.error = error

    def get(self, doc_id: str) -> OcrRecord:
        return self._rec(doc_id)

    def summary(self) -> dict[str, int]:
        out = {s.value: 0 for s in OcrState}
        for r in self._records.values():
            out[r.state.value] += 1
        return out
