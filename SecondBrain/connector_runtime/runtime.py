"""Connector runtime: registry, cursor store, audit, and sync orchestration."""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Protocol

from secondbrain.connector_runtime.connectors import Connector
from secondbrain.connector_runtime.models import (
    AuthError,
    DeadLetter,
    Document,
    ImportJob,
    JobState,
    PermanentError,
    SourceStatus,
    SyncOutcome,
    TransientError,
    compute_status,
    iso,
)
from secondbrain.connector_runtime.oauth import VaultTokenProvider
from secondbrain.connector_runtime.resilience import (
    DeadLetterQueue,
    RateLimiter,
    RetryPolicy,
    run_with_retry,
)

DEFAULT_FRESHNESS_SECONDS = 24 * 3600
MAX_PAGES = 1000


# --- reindex hook --------------------------------------------------------------

class ReindexHook(Protocol):
    def reindex(self, documents: list[Document]) -> dict[str, Any]:
        ...


class NullReindex:
    def reindex(self, documents: list[Document]) -> dict[str, Any]:
        return {"reindexed": 0, "skipped": True}


class CallableReindex:
    """Adapts a plain callable (e.g. a RAG index builder) into a ReindexHook."""

    def __init__(self, fn: Callable[[list[Document]], Any]) -> None:
        self._fn = fn

    def reindex(self, documents: list[Document]) -> dict[str, Any]:
        result = self._fn(documents)
        return result if isinstance(result, dict) else {"reindexed": len(documents)}


# --- persistence ---------------------------------------------------------------

class CursorStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._data: dict[str, dict[str, Any]] = {}
        if self.path.exists():
            self._data = json.loads(self.path.read_text(encoding="utf-8"))

    def get(self, source_id: str) -> dict[str, Any]:
        return self._data.get(source_id, {})

    def update(self, source_id: str, **fields: Any) -> None:
        rec = self._data.setdefault(source_id, {})
        rec.update(fields)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._data, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


class ConnectorAudit:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def record(self, action: str, source_id: str, **detail: Any) -> None:
        entry = {"ts": datetime.now(timezone.utc).isoformat(), "action": action, "source_id": source_id, "detail": detail}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")

    def entries(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        return [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]


class JobStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def append(self, job: ImportJob) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(job.to_dict(), ensure_ascii=False, sort_keys=True) + "\n")

    def entries(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        return [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]


@dataclass
class _Registration:
    source_id: str
    connector: Connector
    freshness_seconds: float


class ConnectorRegistry:
    def __init__(self) -> None:
        self._registry: dict[str, _Registration] = {}

    def register(self, source_id: str, connector: Connector, *, freshness_seconds: float = DEFAULT_FRESHNESS_SECONDS) -> None:
        self._registry[source_id] = _Registration(source_id, connector, freshness_seconds)

    def get(self, source_id: str) -> _Registration:
        if source_id not in self._registry:
            raise KeyError(f"no connector registered for source {source_id!r}")
        return self._registry[source_id]

    def sources(self) -> list[str]:
        return sorted(self._registry)


# --- runtime -------------------------------------------------------------------

class ConnectorRuntime:
    def __init__(
        self,
        runtime_dir: str | Path,
        *,
        registry: ConnectorRegistry | None = None,
        token_provider: VaultTokenProvider | None = None,
        reindex: ReindexHook | None = None,
        retry_policy: RetryPolicy | None = None,
        rate_limiter: RateLimiter | None = None,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        self.dir = Path(runtime_dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.registry = registry or ConnectorRegistry()
        self.token_provider = token_provider
        self.reindex_hook = reindex or NullReindex()
        self.retry_policy = retry_policy or RetryPolicy()
        self.rate_limiter = rate_limiter
        self.sleeper = sleeper
        self.cursors = CursorStore(self.dir / "cursors.json")
        self.dead_letters = DeadLetterQueue(self.dir / "dead_letter.jsonl")
        self.audit = ConnectorAudit(self.dir / "audit.jsonl")
        self.jobs = JobStore(self.dir / "jobs.jsonl")

    def register(self, source_id: str, connector: Connector, *, freshness_seconds: float = DEFAULT_FRESHNESS_SECONDS) -> None:
        self.registry.register(source_id, connector, freshness_seconds=freshness_seconds)

    def _resolve_token(self, source_id: str, connector: Connector) -> str | None:
        if not getattr(connector, "requires_auth", False):
            return None
        if self.token_provider is None:
            raise AuthError(f"connector {connector.name} requires auth but no token provider is configured")
        return self.token_provider.get_access_token(source_id)

    def sync(self, source_id: str) -> SyncOutcome:
        reg = self.registry.get(source_id)
        connector = reg.connector
        job = ImportJob(id=uuid.uuid4().hex[:12], source_id=source_id, connector=connector.name,
                        state=JobState.RUNNING, started_at=time.time())
        self.audit.record("sync_started", source_id, connector=connector.name, job=job.id)

        outcome = SyncOutcome(source_id=source_id, connector=connector.name, job=job)
        cursor = self.cursors.get(source_id).get("cursor")

        try:
            token = self._resolve_token(source_id, connector)
        except AuthError as exc:
            return self._fail(outcome, job, source_id, connector.name, cursor, exc, "auth_error")

        documents: list[Document] = []
        pages = 0
        while pages < MAX_PAGES:
            pages += 1
            if self.rate_limiter is not None:
                self.rate_limiter.acquire()
            try:
                page = run_with_retry(lambda c=cursor: connector.fetch(c, token=token),
                                      self.retry_policy, sleeper=self.sleeper)
            except (AuthError, PermanentError) as exc:
                self._dead_letter(outcome, source_id, connector.name, cursor, exc)
                return self._fail(outcome, job, source_id, connector.name, cursor, exc, "permanent_error")
            except TransientError as exc:
                self._dead_letter(outcome, source_id, connector.name, cursor, exc)
                job.state = JobState.PARTIAL
                break
            documents.extend(page.documents)
            cursor = page.cursor
            if not page.has_more:
                break

        outcome.documents = documents
        outcome.cursor = cursor
        job.documents = len(documents)
        job.dead_letters = len(outcome.dead_letters)

        reindex_result = self.reindex_hook.reindex(documents) if documents else {"reindexed": 0}

        if job.state != JobState.PARTIAL:
            job.state = JobState.SUCCEEDED
        job.finished_at = time.time()
        self.cursors.update(source_id, cursor=cursor, last_sync_ts=job.finished_at, last_error=None,
                            last_status=self._status_value(source_id, job.finished_at, None, reg.freshness_seconds))
        outcome.status = compute_status(job.finished_at, None, freshness_seconds=reg.freshness_seconds)
        self.jobs.append(job)
        self.audit.record("sync_completed", source_id, job=job.id, state=job.state.value,
                          documents=job.documents, dead_letters=job.dead_letters, reindex=reindex_result)
        return outcome

    def _dead_letter(self, outcome: SyncOutcome, source_id: str, connector: str, cursor: str | None, exc: Exception) -> None:
        dl = DeadLetter(source_id=source_id, connector=connector, reference=f"cursor:{cursor}",
                        error=f"{type(exc).__name__}: {exc}", attempts=self.retry_policy.max_attempts)
        self.dead_letters.add(dl)
        outcome.dead_letters.append(dl)
        self.audit.record("dead_letter", source_id, connector=connector, error=dl.error)

    def _fail(self, outcome: SyncOutcome, job: ImportJob, source_id: str, connector: str,
              cursor: str | None, exc: Exception, code: str) -> SyncOutcome:
        job.state = JobState.FAILED
        job.error = f"{code}: {exc}"
        job.dead_letters = len(outcome.dead_letters)
        job.finished_at = time.time()
        self.cursors.update(source_id, cursor=cursor, last_error=job.error, last_status=SourceStatus.ERROR.value)
        outcome.status = SourceStatus.ERROR
        self.jobs.append(job)
        self.audit.record("sync_failed", source_id, job=job.id, error=job.error)
        return outcome

    def _status_value(self, source_id: str, ts: float | None, err: str | None, freshness: float) -> str:
        return compute_status(ts, err, freshness_seconds=freshness).value

    def status(self, source_id: str) -> dict[str, Any]:
        reg = self.registry.get(source_id)
        rec = self.cursors.get(source_id)
        status = compute_status(rec.get("last_sync_ts"), rec.get("last_error"), freshness_seconds=reg.freshness_seconds)
        return {
            "source_id": source_id,
            "connector": reg.connector.name,
            "status": status.value,
            "last_sync_at": iso(rec.get("last_sync_ts")),
            "last_error": rec.get("last_error"),
            "cursor": rec.get("cursor"),
        }

    def statuses(self) -> list[dict[str, Any]]:
        return [self.status(sid) for sid in self.registry.sources()]
