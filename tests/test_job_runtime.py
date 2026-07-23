"""Lifecycle der kanonischen Job-Runtime.

Prueft Factory-Auswahl je Profil, Production-Guard, Doppelstart-Schutz, Shutdown
und Recovery -- ohne echtes PostgreSQL. Die Factory wird injiziert, sodass der
Kontrollfluss deterministisch ist.

Sandbox-Hinweis: der Job-Stack nutzt ``enum.StrEnum`` (Python 3.11). In reinen
3.10-Umgebungen wird ein deckungsgleicher Shim gesetzt, bevor der Stack
importiert wird -- reine Testumgebung, kein Produktionscode.
"""

from __future__ import annotations

import enum

if not hasattr(enum, "StrEnum"):  # pragma: no cover - nur unter Python < 3.11
    class _StrEnum(str, enum.Enum):
        def __str__(self) -> str:
            return str(self.value)
    enum.StrEnum = _StrEnum  # type: ignore[attr-defined]

import threading

import pytest

from secondbrain.jobs.repository import JobRepositoryError
from secondbrain.jobs.runtime import (
    JobRuntime,
    get_job_runtime,
    shutdown_job_runtime,
    start_job_runtime,
)


class _FakeRepo:
    backend = "postgres"

    def __init__(self) -> None:
        self.recovered = 0
        self.shutdown_calls = 0

    def recover_expired_jobs(self, *, now=None):
        self.recovered += 1
        return ["job-1", "job-2"]


def _prod_factory(repo):
    def factory(*, env=None, executor=None):
        return repo
    return factory


def _raising_factory(exc):
    def factory(*, env=None, executor=None):
        raise exc
    return factory


def _none_factory(*, env=None, executor=None):
    return None


# --------------------------------------------------------------------------
# Factory-Auswahl je Profil
# --------------------------------------------------------------------------


def test_production_with_postgres_runs(tmp_path) -> None:
    repo = _FakeRepo()
    rt = JobRuntime(tmp_path, env={"SECONDBRAIN_ENV": "production"},
                    repository_factory=_prod_factory(repo))
    health = rt.start()
    assert health["state"] == "running"
    assert health["backend"] == "postgres"
    assert health["degraded_mode"] is False
    assert health["worker_active"] is True
    assert health["recovered_jobs"] == 2  # Recovery lief beim Start
    rt.shutdown()


def test_development_without_postgres_is_degraded(tmp_path) -> None:
    rt = JobRuntime(tmp_path, env={"SECONDBRAIN_ENV": "development"},
                    repository_factory=_none_factory)
    health = rt.start()
    assert health["state"] == "degraded"
    assert health["degraded_mode"] is True
    assert health["worker_active"] is False
    assert health["reason"] == "jsonl_development_mode"


def test_production_cannot_fall_back_to_jsonl(tmp_path) -> None:
    """Factory liefert None -> Production faellt fail-closed auf blocked, nie degraded-run."""
    rt = JobRuntime(tmp_path, env={"SECONDBRAIN_ENV": "production"},
                    repository_factory=_none_factory)
    health = rt.start()
    assert health["state"] == "blocked"
    assert health["worker_active"] is False


def test_production_guard_error_is_fail_closed_and_redacted(tmp_path) -> None:
    exc = JobRepositoryError("jsonl_not_allowed_in_production dsn=postgres://u:pw@h/db")
    rt = JobRuntime(tmp_path, env={"SECONDBRAIN_ENV": "production"},
                    repository_factory=_raising_factory(exc))
    health = rt.start()
    assert health["state"] == "blocked"
    assert health["worker_active"] is False
    # Nur Fehlerklasse, keine DSN.
    assert health["reason"] == "JobRepositoryError"
    import json
    assert "postgres://" not in json.dumps(health)


# --------------------------------------------------------------------------
# Doppelstart-Schutz
# --------------------------------------------------------------------------


def test_start_is_idempotent(tmp_path) -> None:
    repo = _FakeRepo()
    rt = JobRuntime(tmp_path, env={"SECONDBRAIN_ENV": "production"},
                    repository_factory=_prod_factory(repo))
    rt.start()
    first_worker_id = rt.health()["worker_id"]
    rt.start()  # zweiter Start
    # Recovery lief nur einmal, gleicher Worker.
    assert repo.recovered == 1
    assert rt.health()["worker_id"] == first_worker_id
    rt.shutdown()


def test_singleton_prevents_second_worker(tmp_path) -> None:
    repo = _FakeRepo()
    factory = _prod_factory(repo)
    a = get_job_runtime(tmp_path, env={"SECONDBRAIN_ENV": "production"}, repository_factory=factory)
    b = get_job_runtime(tmp_path, env={"SECONDBRAIN_ENV": "production"}, repository_factory=factory)
    assert a is b
    a.start()
    b.start()
    assert repo.recovered == 1  # kein zweiter Worker, keine zweite Recovery
    shutdown_job_runtime(tmp_path)


def test_worker_id_persists_across_restart(tmp_path) -> None:
    repo1 = _FakeRepo()
    rt1 = JobRuntime(tmp_path, env={"SECONDBRAIN_ENV": "production"}, repository_factory=_prod_factory(repo1))
    wid = rt1.start()["worker_id"]
    rt1.shutdown()
    # Neue Instanz auf derselben Wurzel -> gleiche persistente Worker-ID.
    repo2 = _FakeRepo()
    rt2 = JobRuntime(tmp_path, env={"SECONDBRAIN_ENV": "production"}, repository_factory=_prod_factory(repo2))
    assert rt2.start()["worker_id"] == wid
    rt2.shutdown()


# --------------------------------------------------------------------------
# Shutdown und Pause/Resume
# --------------------------------------------------------------------------


def test_shutdown_is_idempotent_and_clears_worker(tmp_path) -> None:
    rt = JobRuntime(tmp_path, env={"SECONDBRAIN_ENV": "production"}, repository_factory=_prod_factory(_FakeRepo()))
    rt.start()
    h1 = rt.shutdown()
    h2 = rt.shutdown()  # zweiter Shutdown -> kein Fehler
    assert h1["state"] == "stopped" and h2["state"] == "stopped"
    assert rt.health()["worker_active"] is False


def test_shutdown_leaves_no_threads(tmp_path) -> None:
    before = threading.active_count()
    rt = JobRuntime(tmp_path, env={"SECONDBRAIN_ENV": "production"}, repository_factory=_prod_factory(_FakeRepo()))
    rt.start()
    rt.shutdown()
    assert threading.active_count() <= before, "Shutdown hinterliess aktive Threads"


def test_pause_resume(tmp_path) -> None:
    rt = JobRuntime(tmp_path, env={"SECONDBRAIN_ENV": "production"}, repository_factory=_prod_factory(_FakeRepo()))
    rt.start()
    assert rt.pause()["paused"] is True
    assert rt.resume()["paused"] is False
    rt.shutdown()


# --------------------------------------------------------------------------
# Produktiver Einstieg
# --------------------------------------------------------------------------


def test_start_job_runtime_returns_health(tmp_path) -> None:
    health = start_job_runtime(tmp_path, env={"SECONDBRAIN_ENV": "development"},
                               repository_factory=_none_factory)
    assert health["component"] == "job_runtime"
    assert health["state"] in {"running", "degraded", "blocked"}
    shutdown_job_runtime(tmp_path)
