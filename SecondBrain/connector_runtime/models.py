"""Domain models, errors, and status for the connector runtime."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


# --- errors -------------------------------------------------------------------

class ConnectorError(RuntimeError):
    """Base error for connector operations."""


class AuthError(ConnectorError):
    """Credentials missing/invalid. Permanent until re-authenticated (dead-letter)."""


class PermanentError(ConnectorError):
    """Non-retryable error for a specific item/request (dead-letter)."""


class TransientError(ConnectorError):
    """Temporary failure; retry with backoff."""


class RateLimitError(TransientError):
    """Rate limited. ``retry_after`` seconds is honored by the retry policy."""

    def __init__(self, message: str = "rate_limited", retry_after: float = 1.0) -> None:
        super().__init__(message)
        self.retry_after = float(retry_after)


# --- status -------------------------------------------------------------------

class SourceStatus(str, Enum):
    NEVER_SYNCED = "never_synced"
    FRESH = "fresh"
    STALE = "stale"
    ERROR = "error"


class JobState(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    PARTIAL = "partial"
    FAILED = "failed"


def _now() -> float:
    return datetime.now(timezone.utc).timestamp()


def iso(ts: float | None) -> str | None:
    if ts is None:
        return None
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


# --- documents ----------------------------------------------------------------

@dataclass(frozen=True)
class Document:
    """A unit of content produced by a connector, ready for indexing."""

    external_id: str
    source_id: str
    connector: str
    kind: str
    title: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)
    updated_at: float = field(default_factory=_now)

    @property
    def id(self) -> str:
        return f"{self.connector}:{self.external_id}"

    @property
    def checksum(self) -> str:
        return hashlib.sha256(self.text.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "external_id": self.external_id,
            "source_id": self.source_id,
            "connector": self.connector,
            "kind": self.kind,
            "title": self.title,
            "checksum": self.checksum,
            "updated_at": iso(self.updated_at),
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class FetchPage:
    """One page of connector output."""

    documents: list[Document]
    cursor: str | None
    has_more: bool = False


@dataclass
class DeadLetter:
    source_id: str
    connector: str
    reference: str
    error: str
    attempts: int
    ts: float = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "connector": self.connector,
            "reference": self.reference,
            "error": self.error,
            "attempts": self.attempts,
            "ts": iso(self.ts),
        }


@dataclass
class ImportJob:
    id: str
    source_id: str
    connector: str
    state: JobState = JobState.QUEUED
    documents: int = 0
    dead_letters: int = 0
    error: str | None = None
    started_at: float | None = None
    finished_at: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "source_id": self.source_id,
            "connector": self.connector,
            "state": self.state.value,
            "documents": self.documents,
            "dead_letters": self.dead_letters,
            "error": self.error,
            "started_at": iso(self.started_at),
            "finished_at": iso(self.finished_at),
        }


@dataclass
class SyncOutcome:
    source_id: str
    connector: str
    job: ImportJob
    documents: list[Document] = field(default_factory=list)
    cursor: str | None = None
    status: SourceStatus = SourceStatus.FRESH
    dead_letters: list[DeadLetter] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "connector": self.connector,
            "status": self.status.value,
            "job": self.job.to_dict(),
            "documents": [d.to_dict() for d in self.documents],
            "cursor": self.cursor,
            "dead_letters": [d.to_dict() for d in self.dead_letters],
        }


def compute_status(last_sync_ts: float | None, last_error: str | None,
                   *, freshness_seconds: float, now: float | None = None) -> SourceStatus:
    """Derive fresh/stale/error/never from last sync time and last error."""
    if last_error:
        return SourceStatus.ERROR
    if last_sync_ts is None:
        return SourceStatus.NEVER_SYNCED
    current = _now() if now is None else now
    if (current - last_sync_ts) <= freshness_seconds:
        return SourceStatus.FRESH
    return SourceStatus.STALE
