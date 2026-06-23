"""P1.2.6 - Bridge connector sync items into the document ingestion boundary.

The connector lifecycle now produces normalized ``ConnectorItem`` instances.
This bridge converts those items into stable import jobs that can be handed to
an ingestion service without leaking connector-specific payloads into document
storage, indexing, or RAG layers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
from typing import Any, Callable, Iterable, Protocol, runtime_checkable

from .adapter_contract import ConnectorItem
from .adapter_lifecycle import ConnectorLifecycleRun, ConnectorLifecycleService
from .sync_state import SyncIssue, SyncRunResult, SyncStatus


class ImportJobStatus(str, Enum):
    """Stable status values for connector-to-ingestion transfer."""

    PENDING = "pending"
    IMPORTED = "imported"
    SKIPPED = "skipped"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class ConnectorImportJob:
    """Document import request generated from a connector item.

    Invariants:
    - ``job_id`` is deterministic for source/external_id/content_hash.
    - ``document_key`` is stable across content changes for the same source item.
    - ``content_hash`` is preserved for idempotency and incremental ingestion.
    - technical connector metadata remains in ``metadata`` and can be filtered by UI.
    """

    job_id: str
    document_key: str
    source: str
    external_id: str
    title: str
    content: str
    content_hash: str
    updated_at: datetime
    uri: str | None = None
    mime_type: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    status: ImportJobStatus = ImportJobStatus.PENDING

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "document_key": self.document_key,
            "source": self.source,
            "external_id": self.external_id,
            "title": self.title,
            "content": self.content,
            "content_hash": self.content_hash,
            "updated_at": self.updated_at.astimezone(timezone.utc).isoformat(),
            "uri": self.uri,
            "mime_type": self.mime_type,
            "metadata": dict(self.metadata),
            "status": self.status.value,
        }


@dataclass(frozen=True, slots=True)
class ImportBridgeResult:
    """Result of one connector item transfer into ingestion."""

    job: ConnectorImportJob
    status: ImportJobStatus
    message: str = ""

    @property
    def ok(self) -> bool:
        return self.status in {ImportJobStatus.IMPORTED, ImportJobStatus.SKIPPED}

    def to_issue(self) -> SyncIssue:
        return SyncIssue(
            item_id=self.job.external_id,
            code="import_failed",
            message=self.message or "Connector import failed",
            fatal=False,
        )

    def to_dict(self) -> dict[str, Any]:
        return {"job": self.job.to_dict(), "status": self.status.value, "message": self.message, "ok": self.ok}


@runtime_checkable
class ImportJobSink(Protocol):
    """Minimal ingestion boundary consumed by the connector bridge."""

    def submit(self, job: ConnectorImportJob) -> bool:
        """Submit one import job. Return False to skip without failure."""
        ...


class InMemoryImportJobSink:
    """Deterministic sink for tests, dry-runs, and local deployments."""

    def __init__(self, *, fail_on: Iterable[str] = (), skip_existing: bool = True) -> None:
        self.fail_on = set(fail_on)
        self.skip_existing = bool(skip_existing)
        self.jobs: dict[str, ConnectorImportJob] = {}
        self.history: list[ConnectorImportJob] = []

    def submit(self, job: ConnectorImportJob) -> bool:
        if job.external_id in self.fail_on or job.job_id in self.fail_on:
            raise RuntimeError(f"import rejected for {job.external_id}")
        if self.skip_existing and job.job_id in self.jobs:
            self.history.append(job)
            return False
        self.jobs[job.job_id] = job
        self.history.append(job)
        return True


ItemFilter = Callable[[ConnectorItem], bool]


class ConnectorImportBridge:
    """Convert connector items into ingestion jobs with idempotent semantics."""

    def __init__(self, sink: ImportJobSink, *, item_filter: ItemFilter | None = None) -> None:
        self.sink = sink
        self.item_filter = item_filter or (lambda _item: True)
        self.results: list[ImportBridgeResult] = []

    def build_job(self, item: ConnectorItem) -> ConnectorImportJob:
        content_hash = str(item.content_hash or "")
        source = item.source.strip().lower()
        external_id = item.external_id.strip()
        document_key = _stable_key(source, external_id)
        job_id = _stable_key(source, external_id, content_hash)
        return ConnectorImportJob(
            job_id=job_id,
            document_key=document_key,
            source=source,
            external_id=external_id,
            title=item.title,
            content=item.content,
            content_hash=content_hash,
            updated_at=item.updated_at.astimezone(timezone.utc),
            uri=item.uri,
            mime_type=item.mime_type,
            metadata={
                "connector_source": source,
                "connector_external_id": external_id,
                "connector_updated_at": item.updated_at.astimezone(timezone.utc).isoformat(),
                **dict(item.metadata),
            },
        )

    def process_item(self, item: ConnectorItem) -> bool:
        job = self.build_job(item)
        if not self.item_filter(item):
            self.results.append(ImportBridgeResult(job=job, status=ImportJobStatus.SKIPPED, message="filtered"))
            return False
        try:
            accepted = bool(self.sink.submit(job))
        except Exception as exc:  # noqa: BLE001 - item-level import failures must be isolated by lifecycle service
            self.results.append(ImportBridgeResult(job=job, status=ImportJobStatus.FAILED, message=str(exc)))
            raise
        status = ImportJobStatus.IMPORTED if accepted else ImportJobStatus.SKIPPED
        message = "submitted" if accepted else "duplicate_or_unchanged"
        self.results.append(ImportBridgeResult(job=job, status=status, message=message))
        return accepted

    def processor(self) -> Callable[[ConnectorItem], bool]:
        return self.process_item

    def snapshot(self) -> dict[str, Any]:
        imported = sum(1 for result in self.results if result.status == ImportJobStatus.IMPORTED)
        skipped = sum(1 for result in self.results if result.status == ImportJobStatus.SKIPPED)
        failed = sum(1 for result in self.results if result.status == ImportJobStatus.FAILED)
        return {
            "total": len(self.results),
            "imported": imported,
            "skipped": skipped,
            "failed": failed,
            "ok": failed == 0,
            "results": [result.to_dict() for result in self.results],
        }


def run_connector_import(
    lifecycle: ConnectorLifecycleService,
    source: str,
    sink: ImportJobSink,
    *,
    item_filter: ItemFilter | None = None,
) -> tuple[ConnectorLifecycleRun, ConnectorImportBridge]:
    """Run one registered connector and submit its changed items to ingestion."""

    bridge = ConnectorImportBridge(sink=sink, item_filter=item_filter)
    run = lifecycle.run_one(source, bridge.processor())
    return run, bridge


def summarize_import_run(run: ConnectorLifecycleRun, bridge: ConnectorImportBridge) -> dict[str, Any]:
    """Return a compact release-gate friendly connector import summary."""

    bridge_snapshot = bridge.snapshot()
    return {
        "connector": run.result.connector,
        "sync_status": run.result.status.value,
        "fetched": run.result.fetched,
        "processed": run.result.processed,
        "sync_failed": run.result.failed,
        "imported": bridge_snapshot["imported"],
        "skipped": bridge_snapshot["skipped"],
        "import_failed": bridge_snapshot["failed"],
        "ok": run.result.status in {SyncStatus.SUCCESS, SyncStatus.PARTIAL} and bridge_snapshot["failed"] == 0,
        "health": run.health.to_dict(),
    }


def mark_import_failures_on_result(result: SyncRunResult, bridge: ConnectorImportBridge) -> SyncRunResult:
    """Attach failed bridge results as sync issues for callers not using lifecycle retries."""

    for bridge_result in bridge.results:
        if bridge_result.status == ImportJobStatus.FAILED:
            result.add_issue(bridge_result.to_issue())
    return result


def _stable_key(*parts: str) -> str:
    payload = "\x1f".join(str(part or "").strip() for part in parts).encode("utf-8")
    return sha256(payload).hexdigest()
