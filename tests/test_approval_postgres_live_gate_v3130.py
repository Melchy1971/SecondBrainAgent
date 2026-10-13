from __future__ import annotations

import json
import os

import pytest

from launcher import main
from secondbrain.release.approval_postgres_live_gate import (
    BLOCKED, PASS, _binding, _binding_intact, _check, _decision_events, _safe_error,
    run_approval_postgres_live_gate,
)

_TEST_DB = os.environ.get("TEST_DATABASE_URL")


def test_blocks_without_test_database_url(tmp_path) -> None:
    report = run_approval_postgres_live_gate(tmp_path, env={})
    assert report["status"] == BLOCKED
    assert report["backend"] == "not_configured"
    assert "DATABASE_URL" not in json.dumps(report)


def test_rejects_non_postgres_url(tmp_path) -> None:
    report = run_approval_postgres_live_gate(tmp_path, env={"TEST_DATABASE_URL": "sqlite:///test.db"})
    assert report["status"] == BLOCKED
    assert report["failed_checks"] == ["live_execution"]


def test_ignores_production_database_url(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://production.example/prod")
    assert run_approval_postgres_live_gate(tmp_path, env={})["backend"] == "not_configured"


def test_error_redaction_never_exposes_driver_details() -> None:
    error = _safe_error(RuntimeError("host=db.internal user=admin password=secret"))
    assert error["message"] == "live database operation failed"


def test_binding_is_stable_and_detects_mutation() -> None:
    payload = {"workspace": "a", "recipient": "test"}
    assert _binding(payload) == _binding(dict(reversed(list(payload.items()))))
    assert _binding(payload) != _binding({**payload, "recipient": "changed"})


def test_injected_live_success_contains_no_dsn(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(
        "secondbrain.release.approval_postgres_live_gate._run_live",
        lambda _dsn, _schema, _connect: ([{"name": "live", "ok": True}], True),
    )
    report = run_approval_postgres_live_gate(
        tmp_path, env={"TEST_DATABASE_URL": "postgresql://user:secret@private.example/test"},
        connect=lambda _dsn: None,
    )
    assert report["status"] == PASS
    assert "secret" not in json.dumps(report)
    assert "private.example" not in json.dumps(report)


def test_launcher_returns_blocked_without_configuration(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.delenv("TEST_DATABASE_URL", raising=False)
    assert main(["approval-postgres-live-gate", "--project-root", str(tmp_path)]) == 2
    assert '"status": "BLOCKED"' in capsys.readouterr().out


def test_binding_intact_detects_tampered_persisted_payload() -> None:
    bound = {"recipient": "test", "value": "x"}
    item = {"payload": {**bound, "payload_hash": _binding(bound)}}
    assert _binding_intact(item) is True
    item["payload"]["recipient"] = "attacker"
    assert _binding_intact(item) is False
    assert _binding_intact({"payload": bound}) is False      # Hash fehlt
    assert _binding_intact(None) is False


def test_decision_events_ignore_lease_events() -> None:
    class Repo:
        def list_audit_events(self, item_id, *, workspace_id):
            return [{"new_status": s} for s in ("deferred", "approved", "executing", "completed")]

    assert _decision_events(Repo(), "id") == ["deferred", "approved"]


def test_check_detail_is_optional() -> None:
    assert _check("x", True) == {"name": "x", "ok": True}
    assert _check("x", False, "why") == {"name": "x", "ok": False, "detail": "why"}


LIVE_CHECKS = (
    "tls_verify_full", "approve", "restart_persistence", "deferred_then_approved_persisted",
    "concurrent_decisions_single_winner", "concurrent_decisions_with_expected_version",
    "duplicate_decision_not_recorded_twice", "invalid_transition_rejected_rejected_to_approved",
    "invalid_transition_rejected_expired_to_approved", "invalid_transition_rejected_approved_to_rejected",
    "invalid_transition_rejected_completed_to_approved", "cross_workspace_decision_blocked",
    "parallel_exactly_once", "lifecycle_transitions_persisted", "replay_blocked",
    "stale_executor_cannot_complete_after_recovery", "recovery_after_lost_lease",
    "persisted_payload_tamper_detectable",
)


@pytest.mark.skipif(not _TEST_DB, reason="set TEST_DATABASE_URL (sslmode=verify-full) for the live approval run")
def test_approval_gate_live(tmp_path) -> None:
    """Freigaben, konkurrierende Entscheidungen und Zustandsuebergaenge gegen echtes PostgreSQL."""
    pytest.importorskip("psycopg")
    report = run_approval_postgres_live_gate(tmp_path, env={"TEST_DATABASE_URL": _TEST_DB}, write_report=False)
    by_name = {c["name"]: c for c in report["checks"]}
    for name in LIVE_CHECKS:
        assert name in by_name, f"{name} fehlt"
        assert by_name[name]["ok"], f"{name}: {by_name[name].get('detail')}"
    assert report["status"] == PASS and report["evidence"]["cleanup"] is True
    assert _TEST_DB not in json.dumps(report)


class _FakeLive:
    """_Live.parallel ohne Datenbank: fresh() liefert eine Attrappe oder scheitert."""

    def __init__(self, fail_connect: set[int]) -> None:
        from contextlib import contextmanager
        import threading

        from secondbrain.release.approval_postgres_live_gate import _Live

        self._counter = iter(range(100))
        self._lock = threading.Lock()
        self.fail_connect = fail_connect
        live = _Live("postgresql://x/y", "s", connect=lambda _d: None)

        @contextmanager
        def fresh():
            with self._lock:
                index = next(self._counter)
            if index in self.fail_connect:
                raise ConnectionError("simulated: postgresql://u:secret@host/db")
            yield object()

        live.fresh = fresh
        self.live = live


def test_parallel_reports_worker_errors_by_class_only() -> None:
    def task(_repo, index):
        if index % 2:
            raise ValueError("invalid transition with secret detail")
        return {"ok": index}

    results = _FakeLive(set()).live.parallel(4, task)
    assert results[0] == {"ok": 0} and results[2] == {"ok": 2}
    assert results[1] == results[3] == "ValueError"


def test_parallel_does_not_hang_when_a_worker_cannot_connect() -> None:
    import time

    started = time.monotonic()
    results = _FakeLive({0}).live.parallel(3, lambda _repo, i: {"ok": i})
    assert time.monotonic() - started < 10           # nicht bis zum 30-s-Barrieren-Timeout
    assert "ConnectionError" in results
    assert all(r in {"ConnectionError", "BrokenBarrierError"} for r in results)
    assert "secret" not in json.dumps(results)


def test_report_is_sealed_for_aggregation(tmp_path) -> None:
    from secondbrain.release.evidence import canonical_hash

    report = run_approval_postgres_live_gate(tmp_path, env={}, write_report=False)
    assert report["schema"] == "secondbrain.approval_postgres_live_gate.v1"
    assert {"commit_sha", "worktree_clean", "environment", "expires_at"} <= set(report)
    assert report["evidence_sha256"] == canonical_hash(report)
