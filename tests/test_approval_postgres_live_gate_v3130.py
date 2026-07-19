from __future__ import annotations

import json

from launcher import main
from secondbrain.release.approval_postgres_live_gate import (
    BLOCKED, PASS, _binding, _safe_error, run_approval_postgres_live_gate,
)


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
