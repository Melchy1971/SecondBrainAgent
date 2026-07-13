"""ImportJob: die eine Entität für lokale Datei- und Connector-Importe."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from secondbrain.observability.ids import new_job_id


class ImportStatus:
    QUEUED = "queued"
    PARSING = "parsing"
    CLASSIFIED = "classified"
    CHUNKED = "chunked"
    EMBEDDED = "embedded"
    INDEXED = "indexed"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"
    DUPLICATE = "duplicate"
    OCR_REQUIRED = "ocr_required"
    REVIEW_REQUIRED = "review_required"
    FAILED_REVIEWABLE = "failed_reviewable"
    REVIEW_DEFERRED = "review_deferred"
    REJECTED = "rejected"

    ALL = (QUEUED, PARSING, CLASSIFIED, CHUNKED, EMBEDDED, INDEXED,
           FAILED, DEAD_LETTER, DUPLICATE, OCR_REQUIRED, REVIEW_REQUIRED,
           FAILED_REVIEWABLE, REVIEW_DEFERRED, REJECTED)


TERMINAL_STATUSES = frozenset({
    ImportStatus.INDEXED, ImportStatus.DEAD_LETTER,
    ImportStatus.DUPLICATE, ImportStatus.OCR_REQUIRED, ImportStatus.REJECTED,
})
REVIEW_HOLD_STATUSES = frozenset({
    ImportStatus.REVIEW_REQUIRED,
    ImportStatus.FAILED_REVIEWABLE,
    ImportStatus.REVIEW_DEFERRED,
})


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ImportJob:
    source_kind: str                 # "local" | "connector"
    source_ref: str                  # Dateipfad oder Connector-Item-Referenz
    job_id: str = field(default_factory=new_job_id)
    document_id: str = ""
    connector: str = ""              # Connector-Name bei source_kind="connector"
    sync_id: str = ""                # Connector Sync-ID
    correlation_id: str = ""
    status: str = ImportStatus.QUEUED
    attempts: int = 0
    max_attempts: int = 3
    ocr_required: bool = False
    content_hash: str = ""
    duplicate_of: str = ""
    document_type: str = ""          # Ergebnis der Klassifikation
    tags: list[str] = field(default_factory=list)
    confidence: float = 0.0
    chunk_count: int = 0
    error: str = ""
    error_category: str = ""
    parser: str = ""
    review_id: str = ""
    review_category: str = ""
    review_status: str = ""
    review_resume_status: str = ""
    retry_allowed: bool = True
    indexing_blocked: bool = False
    classification_blocked: bool = False
    memory_forwarding_blocked: bool = False
    connector_forwarding_blocked: bool = False
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)
    lineage: dict[str, Any] = field(default_factory=dict)
    stage_history: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.document_id:
            self.document_id = self.job_id

    def transition(self, status: str, detail: str = "") -> None:
        if status not in ImportStatus.ALL:
            raise ValueError(f"unbekannter Import-Status: {status}")
        self.status = status
        self.updated_at = _now()
        entry: dict[str, Any] = {"stage": status, "ts": self.updated_at}
        if detail:
            entry["detail"] = detail[:300]
        self.stage_history.append(entry)

    def resume_after_review(self) -> str:
        """Restore the last processing stage without recording it twice."""

        status = self.review_resume_status or ImportStatus.QUEUED
        if status not in ImportStatus.ALL or status in REVIEW_HOLD_STATUSES:
            status = ImportStatus.QUEUED
        self.status = status
        self.updated_at = _now()
        return status

    @property
    def terminal(self) -> bool:
        return self.status in TERMINAL_STATUSES

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ImportJob":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known})
