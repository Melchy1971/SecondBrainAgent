"""Kanonische Job-Runtime: Lifecycle um die vorhandene Factory und den Worker.

Dieses Modul ist die einzige Stelle, die die Job-Runtime fuer den Produktivbetrieb
instanziiert. Es erzeugt KEINE zweite Factory -- es nutzt ausschliesslich
``create_job_repository`` aus ``SecondBrain/jobs/repository.py``.

Profile
-------
* production: PostgresJobRepository verpflichtend. Fehlt die Konfiguration,
  meldet die Runtime ``blocked`` (fail-closed) und startet keinen Worker.
* development: ohne explizite Konfiguration JSONL -> die Factory liefert ``None``;
  die Runtime laeuft dann sichtbar im ``degraded``-Modus ohne Worker.

Lifecycle
---------
start / health / pause / resume / shutdown / recover. Start und Shutdown sind
idempotent. Ein modulweiter Singleton je Projektwurzel verhindert, dass Desktop,
Tray oder Launcher einen zweiten Worker erzeugen.

Diese Stufe verdrahtet die Runtime kontrolliert -- sie startet keinen dauerhaft
pollenden Hintergrund-Thread. Recovery laeuft beim Start; Batches werden
kontrolliert ausgefuehrt. Dadurch hinterlaesst Shutdown keine Threads oder Locks.
"""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any, Callable, Mapping
from uuid import uuid4

STATE_RUNNING = "running"
STATE_DEGRADED = "degraded"
STATE_BLOCKED = "blocked"
STATE_STOPPED = "stopped"

_DEFAULT_WORKSPACE = "default"


def _is_production(env: Mapping[str, str]) -> bool:
    return str(env.get("SECONDBRAIN_ENV") or "development").lower().startswith("prod")


def _safe_error(exc: BaseException) -> str:
    """Nur die Fehlerklasse -- niemals DSN, Pfad oder Nutzlast."""
    return type(exc).__name__


class JobRuntime:
    """Lifecycle-Huelle um Repository (via Factory) und Worker."""

    def __init__(self, project_root: str | Path = ".", *,
                 env: Mapping[str, str] | None = None,
                 repository_factory: Callable[..., Any] | None = None) -> None:
        self.root = Path(project_root).resolve()
        self._env = dict(os.environ if env is None else env)
        # Genau eine Factory. Injektion nur fuer Tests.
        if repository_factory is None:
            from secondbrain.jobs.repository import create_job_repository
            repository_factory = create_job_repository
        self._factory = repository_factory

        self._lock = threading.RLock()
        self._started = False
        self._paused = False
        self._state = STATE_STOPPED
        self._reason = ""
        self._repository: Any | None = None
        self._worker: Any | None = None
        self._worker_id = ""
        self._recovered: list[str] = []
        self._backend = "none"

    # -- Worker-ID persistiert ueber Prozessneustarts --------------------

    def _worker_id_path(self) -> Path:
        return self.root / "runtime" / "native" / "job_worker.json"

    def _load_or_create_worker_id(self) -> str:
        path = self._worker_id_path()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            wid = str(data.get("worker_id") or "").strip()
            if wid:
                return wid
        except (OSError, json.JSONDecodeError, ValueError):
            pass
        wid = f"native-{uuid4().hex[:16]}"
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps({"worker_id": wid}), encoding="utf-8")
        tmp.replace(path)
        return wid

    # -- Lifecycle -------------------------------------------------------

    def start(self) -> dict[str, Any]:
        """Idempotent. Zweiter Aufruf startet keinen zweiten Worker."""
        with self._lock:
            if self._started:
                return self.health()

            self._worker_id = self._load_or_create_worker_id()
            try:
                repository = self._factory(env=self._env)
            except Exception as exc:  # noqa: BLE001 - Fehlerklasse redigiert
                # Produktionsguard (jsonl verboten, DSN fehlt) -> fail-closed.
                self._state = STATE_BLOCKED
                self._reason = _safe_error(exc)
                self._started = True
                return self.health()

            if repository is None:
                # Entwicklungspfad ohne konfiguriertes PostgreSQL: sichtbar degraded.
                if _is_production(self._env):
                    self._state = STATE_BLOCKED
                    self._reason = "jsonl_not_allowed_in_production"
                else:
                    self._state = STATE_DEGRADED
                    self._reason = "jsonl_development_mode"
                self._started = True
                return self.health()

            self._repository = repository
            self._backend = getattr(repository, "backend", "postgres")
            self._worker = self._build_worker(repository)
            self._recovered = self._recover(repository)
            self._state = STATE_RUNNING
            self._reason = ""
            self._started = True
            return self.health()

    def _build_worker(self, repository: Any) -> Any:
        from secondbrain.jobs.worker import JobHandlerRegistry, JobWorker, WorkerRegistry

        return JobWorker(
            repository, JobHandlerRegistry(), worker_id=self._worker_id,
            workspace_id=_DEFAULT_WORKSPACE, registry=WorkerRegistry(),
        )

    def _recover(self, repository: Any) -> list[str]:
        recover = getattr(repository, "recover_expired_jobs", None)
        if recover is None:
            return []
        try:
            return list(recover())
        except Exception:  # noqa: BLE001 - Recovery darf den Start nicht verhindern
            return []

    def pause(self) -> dict[str, Any]:
        with self._lock:
            if self._state == STATE_RUNNING:
                self._paused = True
            return self.health()

    def resume(self) -> dict[str, Any]:
        with self._lock:
            if self._state == STATE_RUNNING:
                self._paused = False
            return self.health()

    def run_pending(self) -> list[str]:
        """Kontrollierter Batch-Lauf. Kein dauerhafter Hintergrund-Thread."""
        with self._lock:
            if self._state != STATE_RUNNING or self._paused or self._worker is None:
                return []
            worker = self._worker
        done = worker.run_batch()
        return [getattr(job, "job_id", "") for job in done]

    def shutdown(self) -> dict[str, Any]:
        """Idempotent. Hinterlaesst keinen aktiven Worker, keine Lease."""
        with self._lock:
            worker = self._worker
            self._worker = None
            self._repository = None
            self._paused = False
            self._started = False
            self._state = STATE_STOPPED
        if worker is not None:
            try:
                worker.shutdown()
            except Exception:  # noqa: BLE001
                pass
        return self.health()

    def health(self) -> dict[str, Any]:
        with self._lock:
            return {
                "component": "job_runtime",
                "state": self._state,
                "degraded_mode": self._state in {STATE_DEGRADED, STATE_BLOCKED},
                "backend": self._backend,
                "worker_id": self._worker_id,
                "worker_active": self._worker is not None,
                "paused": self._paused,
                "recovered_jobs": len(self._recovered),
                "reason": self._reason,
                "production": _is_production(self._env),
            }


# --------------------------------------------------------------------------
# Singleton je Projektwurzel -- verhindert Doppelstart durch mehrere Aufrufer
# --------------------------------------------------------------------------

_RUNTIMES: dict[str, JobRuntime] = {}
_RUNTIMES_GUARD = threading.RLock()


def get_job_runtime(project_root: str | Path = ".", *,
                    env: Mapping[str, str] | None = None,
                    repository_factory: Callable[..., Any] | None = None) -> JobRuntime:
    """Eine Runtime-Instanz pro Projektwurzel. Wiederholte Aufrufe teilen sie."""
    key = str(Path(project_root).resolve())
    with _RUNTIMES_GUARD:
        runtime = _RUNTIMES.get(key)
        if runtime is None:
            runtime = JobRuntime(project_root, env=env, repository_factory=repository_factory)
            _RUNTIMES[key] = runtime
        return runtime


def start_job_runtime(project_root: str | Path = ".", *,
                      env: Mapping[str, str] | None = None,
                      repository_factory: Callable[..., Any] | None = None) -> dict[str, Any]:
    """Produktiver Einstieg: Runtime holen (Singleton) und idempotent starten."""
    return get_job_runtime(project_root, env=env, repository_factory=repository_factory).start()


def shutdown_job_runtime(project_root: str | Path = ".") -> dict[str, Any] | None:
    key = str(Path(project_root).resolve())
    with _RUNTIMES_GUARD:
        runtime = _RUNTIMES.pop(key, None)
    return runtime.shutdown() if runtime is not None else None
