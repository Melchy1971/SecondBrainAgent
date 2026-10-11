"""Tests fuer die Echtdaten-Aggregation des HUD-Headers (/api/system-truth)."""
from __future__ import annotations

import threading

import pytest

from secondbrain.gui.system_truth import (
    HEALTH_BLOCKED,
    HEALTH_DEGRADED,
    HEALTH_OK,
    CachedSystemTruth,
    build_system_truth,
)
from secondbrain.version import get_version

CURRENT = f"v{get_version()}"


def _view_model(vectors=120, emb_status="pass", prod_ready=True):
    return {
        "provider": {
            "provider": "ollama",
            "status": emb_status,
            "blockers": [] if emb_status != "blocked" else ["embedding_provider_not_production_ready"],
            "provider_status": {"dimensions": 768, "production_ready": prod_ready},
            "config_health": {"config": {"provider": "ollama", "model": "nomic-embed-text", "dimensions": 768}},
        },
        "rag": {"store": {"ok": True, "backend": "postgresql", "documents": 3, "chunks": 9, "vectors": vectors}},
        "job_runtime": {"state": "running"},
    }


def _db_ready():
    return {"status": "ready", "backend": "postgresql", "production_ready": True, "reason": "ok",
            "pgvector": {"postgres_version": "PostgreSQL 16.2", "vector_extension_version": "0.7.0"}}


def _db_sqlite():
    return {"status": "degraded_sqlite", "backend": "sqlite", "production_ready": False,
            "reason": "database_url_missing"}


def _build(*, vm=None, db=None, gate=None, backup=None, memory=None, models=("llama3.1",),
           env=None):
    return build_system_truth(
        ".",
        release_gate=lambda: gate if gate is not None else {"status": "PASS", "blockers": [], "version": CURRENT,
                                                            "timestamp": "2026-10-09T08:00:00+00:00"},
        ollama_models=lambda: list(models),
        ollama_url="http://localhost:11434",
        view_model=lambda _root: vm if vm is not None else _view_model(),
        db_status=lambda _root: db if db is not None else _db_ready(),
        backup_snapshot=lambda _root: backup if backup is not None else {
            "backup_center": {"status": "PASS", "backup_count": 2,
                              "latest_backup": {"created_at": "2026-10-08T22:00:00+00:00"}},
            "scheduler": {"enabled": True, "interval": "daily"}},
        memory_status=lambda _root: memory if memory is not None else {
            "status": "pass", "summary": {"total_memories": 10, "vault_memories": 8, "sqlite_memories": 2}},
        env=env if env is not None else {"SECOND_BRAIN_ENV": "production"},
    )


def test_all_green_reports_ok_with_real_values():
    t = _build()

    assert t["ok"] is True and t["version"] == CURRENT
    assert t["health"] == {"level": HEALTH_OK, "text": "Alle Prüfungen bestanden", "blockers": [], "warnings": []}
    assert t["database"]["label"] == "PostgreSQL"
    assert t["database"]["pgvector_version"] == "0.7.0"
    assert t["embedding"] == {"provider": "ollama", "model": "nomic-embed-text", "dimensions": 768,
                              "status": "pass", "production_ready": True, "blockers": []}
    assert t["vector_index"]["status"] == "ok" and t["vector_index"]["vectors"] == 120
    assert t["backup"]["last_at"] == "2026-10-08T22:00:00+00:00"
    assert t["job_queue"] == {"backend": "postgresql", "state": "running", "pending": None}
    assert t["ollama"] == {"url": "http://localhost:11434", "models": 1}


def test_sqlite_in_production_is_blocker_and_queue_inactive():
    t = _build(db=_db_sqlite())

    assert t["health"]["level"] == HEALTH_BLOCKED
    assert "database:degraded_sqlite" in t["health"]["blockers"]
    assert t["database"]["label"] == "SQLite" and t["database"]["pgvector_version"] is None
    assert t["job_queue"] == {"backend": None, "state": "inactive", "pending": None}


def test_sqlite_in_development_is_only_warning():
    t = _build(db=_db_sqlite(), env={"SECOND_BRAIN_ENV": "development"})

    assert t["environment"] == "development"
    assert t["health"]["level"] == HEALTH_DEGRADED
    assert "database:degraded_sqlite" in t["health"]["warnings"]


def test_release_gate_blockers_are_listed_individually():
    t = _build(gate={"status": "BLOCKED", "blockers": ["production_backend", "postgresql_health"],
                     "version": CURRENT})

    assert t["health"]["blockers"] == ["release_gate:production_backend", "release_gate:postgresql_health"]


def test_release_gate_blocked_without_details_still_blocks():
    t = _build(gate={"status": "BLOCKED", "blockers": [], "version": CURRENT})

    assert t["health"]["blockers"] == ["release_gate"]


@pytest.mark.parametrize("gate,stale", [
    ({"status": "PASS", "blockers": [], "version": "v30.86"}, True),
    ({"status": "PASS", "blockers": [], "version": CURRENT.lstrip("v")}, False),
    ({"status": "PASS", "blockers": []}, False),
])
def test_release_gate_report_from_other_version_is_stale(gate, stale):
    t = _build(gate=gate)

    assert t["release_gate"]["stale"] is stale
    assert ("release_gate_report_outdated" in t["health"]["warnings"]) is stale


def test_release_gate_not_run_is_warning():
    t = _build(gate={"ok": True, "status": "not_run", "report": None})

    assert t["health"]["level"] == HEALTH_DEGRADED
    assert "release_gate_report_outdated" in t["health"]["warnings"]


def test_blocked_embedding_is_blocker():
    t = _build(vm=_view_model(emb_status="blocked", prod_ready=False))

    assert "embedding:blocked" in t["health"]["blockers"]
    assert t["embedding"]["blockers"] == ["embedding_provider_not_production_ready"]


def test_degraded_signals_are_warnings():
    t = _build(vm=_view_model(vectors=0), models=(),
               backup={"backup_center": {"status": "CONDITIONAL_PASS", "backup_count": 0, "latest_backup": None},
                       "scheduler": {"enabled": False, "last_success_at": ""}},
               memory={"status": "blocked", "summary": {"total_memories": 10}})

    assert t["health"]["level"] == HEALTH_DEGRADED
    assert set(t["health"]["warnings"]) == {"vector_index:empty", "backup:none", "memory:governance_blocked",
                                            "ollama:unreachable"}
    assert t["backup"]["last_at"] is None and t["backup"]["interval"] is None


def test_missing_sources_yield_unknown_not_invented_values():
    t = _build(vm={}, db={}, gate={}, backup={}, memory={})

    assert t["database"]["status"] == "unknown" and t["database"]["production_ready"] is False
    assert t["embedding"]["provider"] == "unknown" and t["embedding"]["dimensions"] is None
    assert t["vector_index"]["status"] == "error"
    assert t["backup"]["count"] == 0 and t["backup"]["last_at"] is None
    assert t["health"]["level"] == HEALTH_BLOCKED


def test_cache_reuses_value_within_ttl_and_rebuilds_after():
    now = [0.0]
    calls = []
    cache = CachedSystemTruth(lambda: calls.append(1) or {"n": len(calls)}, ttl_seconds=30, clock=lambda: now[0])

    assert cache.get() == {"n": 1}
    now[0] = 29.9
    assert cache.get() == {"n": 1}
    now[0] = 30.0
    assert cache.get() == {"n": 2}


def test_cache_builds_once_under_concurrent_first_access():
    calls = []
    gate = threading.Event()

    def slow():
        gate.wait(1)
        calls.append(1)
        return {"ok": True}

    cache = CachedSystemTruth(slow, ttl_seconds=60)
    threads = [threading.Thread(target=cache.get) for _ in range(8)]
    for th in threads:
        th.start()
    gate.set()
    for th in threads:
        th.join()

    assert len(calls) == 1


def test_cache_does_not_store_failures():
    attempts = []

    def flaky():
        attempts.append(1)
        if len(attempts) == 1:
            raise RuntimeError("transient")
        return {"ok": True}

    cache = CachedSystemTruth(flaky)
    with pytest.raises(RuntimeError):
        cache.get()
    assert cache.get() == {"ok": True}
