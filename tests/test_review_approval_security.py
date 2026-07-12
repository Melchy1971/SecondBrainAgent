from __future__ import annotations

import json

from secondbrain.agent.review_approval_gate import (
    BLOCKED,
    CONDITIONAL_PASS,
    PASS,
    GateCheck,
    evaluate_gate_status,
    run_review_approval_gate,
)


def test_hard_security_failure_blocks_gate() -> None:
    checks = [GateCheck("unapproved_execution", "No bypass", False, "tool executed", hard_blocker=True)]

    assert evaluate_gate_status(checks) == BLOCKED


def test_non_blocking_operability_failure_is_conditional() -> None:
    checks = [GateCheck("viewmodel", "ViewModel", False, "view unavailable")]

    assert evaluate_gate_status(checks) == CONDITIONAL_PASS
    assert evaluate_gate_status([GateCheck("ok", "OK", True, "passed")]) == PASS


def test_gate_enforces_mandatory_actions_redaction_and_audit(tmp_path) -> None:
    report = run_review_approval_gate(tmp_path)
    checks = {check["check_id"]: check for check in report["checks"]}

    for check_id in (
        "delete_requires_approval",
        "send_requires_approval",
        "external_write_requires_approval",
        "sensitive_payload_redacted",
        "decision_audit",
    ):
        assert checks[check_id]["status"] == PASS
    assert "gate-secret-value-9f31" not in json.dumps(report, ensure_ascii=False)


def test_gate_handles_corruption_and_reports_parallel_decision_conflict(tmp_path) -> None:
    report = run_review_approval_gate(tmp_path)
    checks = {check["check_id"]: check for check in report["checks"]}

    assert checks["corrupt_queue_controlled"]["status"] == PASS
    assert checks["parallel_decision_conflict_safe"]["status"] == CONDITIONAL_PASS
    assert "accepted=2" in checks["parallel_decision_conflict_safe"]["detail"]
