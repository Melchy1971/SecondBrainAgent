from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from secondbrain.agent.review_approval_gate import CONDITIONAL_PASS, PASS, run_review_approval_gate


EXPECTED_CHECKS = {
    "low_risk_direct",
    "risky_tool_pauses",
    "approval_persisted",
    "viewmodel_visible",
    "approve_exactly_once",
    "reject_prevents_execution",
    "defer_holds_plan",
    "delete_requires_approval",
    "send_requires_approval",
    "external_write_requires_approval",
    "sensitive_payload_redacted",
    "decision_audit",
    "restart_retains_pending",
    "corrupt_queue_controlled",
    "parallel_decision_conflict_safe",
}


@pytest.fixture(scope="module")
def gate_report(tmp_path_factory: pytest.TempPathFactory) -> dict[str, object]:
    return run_review_approval_gate(tmp_path_factory.mktemp("review-approval-gate"))


def test_review_approval_gate_reports_all_e2e_checks(gate_report: dict[str, object]) -> None:
    checks = gate_report["checks"]
    assert gate_report["status"] == CONDITIONAL_PASS
    assert gate_report["ok"] is True
    assert gate_report["summary"] == {"total": 15, "passed": 14, "conditional": 1, "blocked": 0}
    assert {check["check_id"] for check in checks} == EXPECTED_CHECKS
    assert all(
        check["status"] == (CONDITIONAL_PASS if check["check_id"] == "parallel_decision_conflict_safe" else PASS)
        for check in checks
    )
    assert gate_report["blockers"] == []
    assert len(gate_report["warnings"]) == 1


def test_gate_covers_pause_decide_resume_and_inbox(gate_report: dict[str, object]) -> None:
    checks = {check["check_id"]: check for check in gate_report["checks"]}
    for check_id in (
        "risky_tool_pauses",
        "approval_persisted",
        "viewmodel_visible",
        "approve_exactly_once",
        "reject_prevents_execution",
        "defer_holds_plan",
        "restart_retains_pending",
    ):
        assert checks[check_id]["passed"] is True


def test_launcher_exposes_review_approval_gate(tmp_path: Path) -> None:
    repository_root = Path(__file__).resolve().parents[1]
    completed = subprocess.run(
        [
            sys.executable,
            str(repository_root / "launcher.py"),
            "review-approval-gate",
            "--project-root",
            str(tmp_path),
        ],
        cwd=repository_root,
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert completed.returncode == 0, completed.stderr
    report = json.loads(completed.stdout)
    assert report["status"] == CONDITIONAL_PASS
    assert report["summary"]["total"] == 15
