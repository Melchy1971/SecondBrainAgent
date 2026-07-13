"""Prompt 16 - final security and release gate for review/approval governance."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from secondbrain.agent.review_approval_release_gate import (
    RELEASE_VERSION,
    SCHEMA,
    run_review_approval_release_gate,
)

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
}


@pytest.fixture(scope="module")
def report(tmp_path_factory) -> dict:
    root = tmp_path_factory.mktemp("release-gate")
    return run_review_approval_release_gate(root)


def test_gate_passes(report):
    assert report["overall_status"] == "PASS"
    assert report["blockers"] == []
    assert report["summary"]["blocked"] == 0
    assert report["summary"]["total"] == report["summary"]["passed"]


def test_report_contains_all_required_fields(report):
    assert REQUIRED_FIELDS.issubset(report.keys())
    assert report["schema"] == SCHEMA
    assert report["version"] == RELEASE_VERSION
    assert report["test_commands"]


def test_security_summary_all_pass(report):
    assert report["security_summary"]
    assert all(status == "PASS" for status in report["security_summary"].values())
    # Core security guarantees are represented.
    for check_id in ("delete_requires_approval", "memory_privacy_mode_blocked", "no_double_execution"):
        assert report["security_summary"].get(check_id) == "PASS"


def test_backend_status_present(report):
    assert "configured_backend" in report["backend_status"]
    assert report["backend_status"]["postgres_healthy"] is True
    assert report["backend_status"]["jsonl_production_degraded"] is True


def test_report_is_written_to_disk(tmp_path):
    run_review_approval_release_gate(tmp_path)
    path = tmp_path / "runtime" / "reports" / "review_approval_release_gate.json"
    assert path.exists()
    persisted = json.loads(path.read_text(encoding="utf-8"))
    assert persisted["overall_status"] == "PASS"


def test_report_contains_no_secrets(report):
    blob = json.dumps(report, ensure_ascii=False)
    assert "hunter2" not in blob
    assert "password=" not in blob


def test_launcher_exposes_release_gate(tmp_path):
    completed = subprocess.run(
        [sys.executable, "launcher.py", "review-approval-release-gate", "--project-root", str(tmp_path)],
        cwd=str(Path(__file__).resolve().parents[1]),
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["overall_status"] == "PASS"
    assert payload["schema"] == SCHEMA
