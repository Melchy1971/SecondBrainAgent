"""Production certification tests for review/approval governance v30.86."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from secondbrain.agent.review_approval_release_gate import (
    RELEASE_VERSION,
    SCHEMA,
    run_review_approval_release_gate,
)
from secondbrain.storage.db_executor import SqliteExecutor

REQUIRED_FIELDS = {
    "schema",
    "version",
    "timestamp",
    "overall_status",
    "checks",
    "blockers",
    "warnings",
    "metrics",
    "test_commands",
    "backend_status",
    "security_summary",
    "release_recommendation",
}

REQUIRED_GROUPS = {
    "data_model", "agent", "security", "import", "memory",
    "connector", "operations", "gui",
}

CRITICAL_CHECKS = {
    "review_item_model",
    "approval_item_model",
    "status_transitions",
    "optimistic_versioning",
    "workspace_isolation",
    "risky_tool_pauses",
    "approve_exactly_once",
    "reject_prevents_execution",
    "defer_holds_plan",
    "delete_requires_approval",
    "send_requires_approval",
    "external_write_requires_approval",
    "credential_change_requires_approval",
    "scope_change_requires_approval",
    "confirmed_boolean_blocked",
    "import_failed_review",
    "import_sensitive_review",
    "import_low_confidence_review",
    "import_approve_resumes",
    "import_reject_stops",
    "import_defer_pauses",
    "import_no_duplicates",
    "memory_sensitive_blocked",
    "memory_low_confidence_review",
    "memory_privacy_mode_blocked",
    "memory_no_secret_leak",
    "memory_approve_once",
    "connector_scope_diff_bound",
    "connector_payload_bound",
    "connector_workspace_bound",
    "connector_expiration_enforced",
    "connector_single_use",
    "decision_audit",
    "no_double_execution",
    "crash_recovery_status",
    "corrupt_queue_recoverable",
    "production_backend",
    "postgresql_health",
    "repository_health",
    "gui_no_secret_leak",
}


@pytest.fixture(scope="module")
def report(tmp_path_factory) -> dict:
    root = tmp_path_factory.mktemp("release-gate")
    return run_review_approval_release_gate(
        root,
        env={"REVIEW_APPROVAL_BACKEND": "postgres"},
        repository_executor=SqliteExecutor(":memory:"),
    )


def test_gate_certifies_all_critical_checks(report):
    assert report["overall_status"] == "PASS"
    assert report["blockers"] == []
    assert report["warnings"] == []
    assert report["release_recommendation"] == "RELEASE"
    statuses = {check["check_id"]: check["status"] for check in report["checks"]}
    assert CRITICAL_CHECKS.issubset(statuses)
    assert all(statuses[check_id] == "PASS" for check_id in CRITICAL_CHECKS)


def test_report_contains_required_fields_and_groups(report):
    assert REQUIRED_FIELDS.issubset(report)
    assert report["schema"] == SCHEMA
    assert report["version"] == RELEASE_VERSION == "v30.86"
    assert report["summary"]["total"] >= 50
    assert report["summary"]["total"] == report["summary"]["passed"]
    assert {check["group"] for check in report["checks"]} == REQUIRED_GROUPS
    assert report["test_commands"][0] == "python launcher.py review-approval-release-gate"


def test_security_summary_all_pass(report):
    assert report["security_summary"]
    assert all(status == "PASS" for status in report["security_summary"].values())
    for check_id in (
        "delete_requires_approval",
        "confirmed_boolean_blocked",
        "memory_privacy_mode_blocked",
        "connector_workspace_bound",
        "no_double_execution",
    ):
        assert report["security_summary"].get(check_id) == "PASS"


def test_postgres_backend_is_production_eligible(report):
    backend = report["backend_status"]
    assert backend["configured_backend"] == "postgres"
    assert backend["postgres_healthy"] is True
    assert backend["production_eligible"] is True
    assert backend["gate_status"] == "PASS"
    assert backend["jsonl_production_degraded"] is True


def test_jsonl_backend_is_a_hard_blocker(tmp_path):
    report = run_review_approval_release_gate(
        tmp_path,
        write_report=False,
        env={"REVIEW_APPROVAL_BACKEND": "jsonl"},
    )

    assert report["overall_status"] == "BLOCKED"
    assert report["release_recommendation"] == "DO_NOT_RELEASE"
    assert "production_backend" in report["blockers"]
    assert report["backend_status"]["production_eligible"] is False


def test_unreachable_postgres_is_blocked_without_fallback(tmp_path):
    report = run_review_approval_release_gate(
        tmp_path,
        write_report=False,
        env={"REVIEW_APPROVAL_BACKEND": "postgres"},
    )

    assert report["overall_status"] == "BLOCKED"
    assert "postgresql_health" in report["blockers"]
    assert report["backend_status"]["configured_backend"] == "postgres"
    assert report["backend_status"]["postgres_healthy"] is False


def test_report_is_written_atomically(tmp_path):
    report = run_review_approval_release_gate(
        tmp_path,
        env={"REVIEW_APPROVAL_BACKEND": "postgres"},
        repository_executor=SqliteExecutor(":memory:"),
    )
    path = tmp_path / "runtime" / "reports" / "review_approval_release_gate.json"

    assert path.exists()
    assert not path.with_suffix(path.suffix + ".tmp").exists()
    assert json.loads(path.read_text(encoding="utf-8")) == report


def test_report_contains_no_secrets(report):
    blob = json.dumps(report, ensure_ascii=False).lower()
    for forbidden in (
        "hunter2", "release-gate-secret-value", "password=", "api_key=", "private key",
    ):
        assert forbidden not in blob


def test_launcher_blocks_jsonl_and_writes_report(tmp_path):
    environment = dict(os.environ)
    environment["REVIEW_APPROVAL_BACKEND"] = "jsonl"
    completed = subprocess.run(
        [
            sys.executable,
            "launcher.py",
            "review-approval-release-gate",
            "--project-root",
            str(tmp_path),
        ],
        cwd=str(Path(__file__).resolve().parents[1]),
        env=environment,
        capture_output=True,
        text=True,
        timeout=120,
    )

    assert completed.returncode == 2, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["overall_status"] == "BLOCKED"
    assert payload["release_recommendation"] == "DO_NOT_RELEASE"
    assert (tmp_path / "runtime" / "reports" / "review_approval_release_gate.json").exists()
