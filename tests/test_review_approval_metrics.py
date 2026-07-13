"""Prompt 13 - governance metrics for review/approval.

Acceptance coverage:
  1. Metrics are correct for an empty queue.
  2. Approve/Reject/Defer are counted correctly.
  3. Decision times are computed correctly.
  4. Category aggregation is correct.
  5. Corrupted audit lines do not break the calculation.
  6. No secrets or payloads leak into the export.
  7. The dashboard view model contains all core figures.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

from secondbrain.agent.review_service import UnifiedReviewInbox
from secondbrain.metrics.review_approval_metrics import ReviewApprovalMetrics
from secondbrain.native.approval import (
    ApprovalConcurrencyError,
    NativeApprovalQueue,
    ReviewQueue,
    approval_path,
    review_path,
)
from secondbrain.native.dashboard_center.service import NativeDashboardService
from secondbrain.native.runtime_snapshot import build_native_view_model

REVIEW_SCHEMA = "secondbrain.native.review_queue.v1"


def _write_reviews(root, records):
    path = review_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _review(review_id, category, status, created, decided=None, **extra):
    record = {
        "schema": REVIEW_SCHEMA,
        "review_id": review_id,
        "created_at": created,
        "category": category,
        "status": status,
        "title": "x",
        "source": "importer",
        "metadata": {},
    }
    if decided:
        record["decided_at"] = decided
    record.update(extra)
    return record


# -- 1 ---------------------------------------------------------------------

def test_metrics_are_zero_for_empty_queue(tmp_path):
    result = ReviewApprovalMetrics(tmp_path).compute()

    assert result.volume["created_total"] == 0
    assert result.volume["approved_total"] == 0
    assert result.times["average_decision_time"] == 0.0
    assert result.times["p95_decision_time"] == 0.0
    assert result.quality["approval_rate"] == 0.0
    assert result.volume["recovery_required_total"] == 0
    for key in (
        "blocked_unsafe_execution_count",
        "duplicate_execution_prevented_count",
        "stale_decision_conflict_count",
        "secret_redaction_count",
        "privacy_block_count",
        "workspace_mismatch_count",
    ):
        assert result.security[key] == 0
    for key in ("resume_success_rate", "resume_failure_rate", "review_reopen_rate"):
        assert result.quality[key] == 0.0
    assert result.corrupted_audit_lines == 0


# -- 2 ---------------------------------------------------------------------

def test_approve_reject_defer_are_counted(tmp_path):
    approvals = NativeApprovalQueue(tmp_path)
    reviews = ReviewQueue(tmp_path)
    approval = approvals.create(command="records.delete", intent="del", text="Del", category="delete_request", risk_level="high")
    r_reject = reviews.create(category="sensitive_document", title="S", source="c")
    r_defer = reviews.create(category="failed_import", title="I", source="c")
    inbox = UnifiedReviewInbox(tmp_path)
    inbox.approve(approval["approval_id"], "markus", "ok")
    inbox.reject(r_reject["review_id"], "markus", "no")
    inbox.defer(r_defer["review_id"], "markus", until=(datetime.now(timezone.utc) + timedelta(hours=5)).isoformat(), note="x")

    result = ReviewApprovalMetrics(inbox=UnifiedReviewInbox(tmp_path)).compute()

    assert result.volume["created_total"] == 3
    assert result.volume["approved_total"] == 1
    assert result.volume["rejected_total"] == 1
    assert result.volume["deferred_total"] == 1
    assert result.quality["approval_rate"] == pytest.approx(1 / 3, abs=1e-3)
    assert result.quality["rejection_rate"] == pytest.approx(1 / 3, abs=1e-3)
    assert result.quality["defer_rate"] == pytest.approx(1 / 3, abs=1e-3)


# -- 3 ---------------------------------------------------------------------

def test_decision_times_are_computed(tmp_path):
    base = "2026-07-13T12:00:00+00:00"
    _write_reviews(
        tmp_path,
        [
            _review("r1", "failed_import", "approved", base, "2026-07-13T12:01:40+00:00"),  # 100s
            _review("r2", "failed_import", "approved", base, "2026-07-13T12:05:00+00:00"),  # 300s
            _review("r3", "failed_import", "rejected", base, "2026-07-13T12:03:20+00:00"),  # 200s
        ],
    )

    result = ReviewApprovalMetrics(tmp_path).compute()

    assert result.times["average_decision_time"] == pytest.approx(200.0)
    assert result.times["median_decision_time"] == pytest.approx(200.0)
    assert result.times["p95_decision_time"] == pytest.approx(290.0, abs=1.0)


def test_deferred_duration_uses_audited_lifecycle(tmp_path):
    base = "2026-07-13T12:00:00+00:00"
    _write_reviews(
        tmp_path,
        [
            _review(
                "r-deferred",
                "failed_import",
                "approved",
                base,
                "2026-07-13T14:00:00+00:00",
                decision_audit=[
                    {"old_status": "pending", "new_status": "deferred", "timestamp": base},
                    {
                        "old_status": "deferred",
                        "new_status": "approved",
                        "timestamp": "2026-07-13T14:00:00+00:00",
                    },
                ],
            )
        ],
    )

    result = ReviewApprovalMetrics(tmp_path).compute()

    assert result.times["average_deferred_duration"] == 7200.0


# -- 4 ---------------------------------------------------------------------

def test_category_aggregation(tmp_path):
    base = "2026-07-13T12:00:00+00:00"
    _write_reviews(
        tmp_path,
        [
            _review("r1", "sensitive_document", "pending", base),
            _review("r2", "sensitive_document", "pending", base),
            _review("r3", "failed_import", "pending", base),
        ],
    )

    result = ReviewApprovalMetrics(tmp_path).compute()

    assert result.segments["category"]["sensitive_document"] == 2
    assert result.segments["category"]["failed_import"] == 1
    # Segmentation dimensions are all present.
    for dimension in ("category", "tool", "connector", "workspace", "risk", "source"):
        assert dimension in result.segments
    assert "time_range" in result.segments


def test_all_segment_dimensions_use_sanitized_operational_fields(tmp_path):
    NativeApprovalQueue(tmp_path).create(
        command="connector.upload",
        intent="upload",
        text="Upload",
        category="connector_permission_change",
        risk_level="high",
        tool_name="connector.upload",
        workspace_id="workspace-blue",
        payload={"connector_id": "drive", "body": "document-content"},
    )

    result = ReviewApprovalMetrics(tmp_path).compute()

    assert result.segments["category"] == {"connector_permission_change": 1}
    assert result.segments["risk"] == {"high": 1}
    assert result.segments["tool"] == {"connector.upload": 1}
    assert result.segments["connector"] == {"drive": 1}
    assert result.segments["workspace"] == {"workspace-blue": 1}
    assert result.segments["source"] == {"approval": 1}
    assert sum(result.segments["time_range"].values()) == 1


# -- 5 ---------------------------------------------------------------------

def test_corrupted_audit_lines_do_not_break_calculation(tmp_path):
    native = tmp_path / "runtime" / "native"
    native.mkdir(parents=True, exist_ok=True)
    audit = native / "memory_governance_audit.jsonl"
    audit.write_text(
        "\n".join(
            [
                json.dumps({"decision": "blocked", "reason": "secret_blocked"}),
                "{ this is not valid json",
                "",
                json.dumps({"decision": "duplicate"}),
                "also-garbage}}}",
            ]
        ),
        encoding="utf-8",
    )

    result = ReviewApprovalMetrics(tmp_path).compute()

    assert result.corrupted_audit_lines == 2
    assert result.quality["blocked_unsafe_execution_count"] == 1
    assert result.quality["duplicate_prevention_count"] == 1
    assert result.quality["secret_redaction_count"] == 1


def test_security_and_quality_audit_metrics(tmp_path):
    base = "2026-07-13T12:00:00+00:00"
    _write_reviews(tmp_path, [_review("resolved", "failed_import", "approved", base, base)])
    native = tmp_path / "runtime" / "native"
    audit = native / "review_approval_audit.jsonl"
    rows = [
        {"status": "blocked", "reason": "mandatory_approval"},
        {"event": "duplicate_execution_prevented"},
        {"error": "approval_version_conflict"},
        {"reason": "secret_redacted"},
        {"reason": "privacy_mode_active"},
        {"error": "workspace_mismatch"},
        {"command": "resume_approval", "status": "completed"},
        {"command": "resume_approval", "status": "failed"},
        {"event": "review_reopened"},
    ]
    audit.write_text(
        "\n".join([*(json.dumps(row) for row in rows), "broken-json{"]),
        encoding="utf-8",
    )

    result = ReviewApprovalMetrics(tmp_path).compute()

    assert result.security == {
        "blocked_unsafe_execution_count": 1,
        "duplicate_execution_prevented_count": 1,
        "stale_decision_conflict_count": 1,
        "secret_redaction_count": 1,
        "privacy_block_count": 1,
        "workspace_mismatch_count": 1,
    }
    assert result.quality["resume_success_rate"] == 0.5
    assert result.quality["resume_failure_rate"] == 0.5
    assert result.quality["review_reopen_rate"] == 1.0
    assert result.corrupted_audit_lines == 1


def test_recovery_required_volume_is_counted(tmp_path):
    queue = NativeApprovalQueue(tmp_path)
    approval = queue.create(
        command="data.read",
        intent="read",
        text="Read",
        risk_level="low",
        tool_name="data.read",
    )
    queue.transition(approval["approval_id"], "approved", actor="reviewer")
    queue.begin_execution(approval["approval_id"], executor_id="crashed", lease_seconds=1)
    queue.recover_stale_leases(now=datetime.now(timezone.utc) + timedelta(days=1))

    result = ReviewApprovalMetrics(tmp_path).compute()

    assert result.volume["recovery_required_total"] == 1
    assert result.volume["approved_total"] == 1


def test_real_guards_feed_conflict_and_duplicate_metrics(tmp_path):
    queue = NativeApprovalQueue(tmp_path)
    approval = queue.create(command="data.read", intent="read", text="Read", risk_level="low")
    queue.transition(approval["approval_id"], "approved", actor="reviewer", expected_version=0)

    with pytest.raises(ApprovalConcurrencyError):
        queue.transition(
            approval["approval_id"],
            "rejected",
            actor="stale-reviewer",
            expected_version=0,
        )
    queue.begin_execution(approval["approval_id"], executor_id="worker-1")
    with pytest.raises(ApprovalConcurrencyError):
        queue.begin_execution(approval["approval_id"], executor_id="worker-2")

    security = ReviewApprovalMetrics(tmp_path).compute().security

    assert security["stale_decision_conflict_count"] == 1
    assert security["duplicate_execution_prevented_count"] == 1


# -- 6 ---------------------------------------------------------------------

def test_export_contains_no_secrets_or_payloads(tmp_path):
    approvals = NativeApprovalQueue(tmp_path)
    secret = "hunter2_TOP_SECRET"
    approvals.create(
        command="connector.push",
        intent="send",
        text="Send data",
        category="external_send",
        tool_name=f"password={secret}",
        workspace_id=f"secret={secret}",
        payload={"password": secret, "body": "personal-content"},
    )

    export = ReviewApprovalMetrics(tmp_path).export()
    blob = json.dumps(export, ensure_ascii=False)

    assert secret not in blob
    assert "personal-content" not in blob
    assert "payload" not in blob
    assert "password=" not in blob


def test_export_carries_no_technical_ids(tmp_path):
    reviews = ReviewQueue(tmp_path)
    created = reviews.create(category="failed_import", title="Secret Title", source="c")

    blob = json.dumps(ReviewApprovalMetrics(tmp_path).export(), ensure_ascii=False)

    assert created["review_id"] not in blob
    assert "Secret Title" not in blob


# -- 7 ---------------------------------------------------------------------

def test_dashboard_view_model_contains_core_figures(tmp_path):
    NativeApprovalQueue(tmp_path).create(command="records.delete", intent="del", text="Del", category="delete_request", risk_level="high")
    ReviewQueue(tmp_path).create(category="sensitive_document", title="S", source="c")

    snapshot = build_native_view_model(tmp_path)

    assert "governance_metrics" in snapshot
    core = snapshot["governance_metrics"]
    for key in (
        "open_items",
        "critical_items",
        "overdue_items",
        "blocked_unsafe_actions",
        "open_approvals",
        "critical_approvals",
        "overdue_reviews",
        "average_decision_time",
        "blocked_unsafe_executions",
        "most_common_category",
        "trend_7d",
        "trend_30d",
    ):
        assert key in core


def test_dashboard_service_exposes_governance_card(tmp_path):
    NativeApprovalQueue(tmp_path).create(command="records.delete", intent="del", text="Del", category="delete_request", risk_level="high")

    cards = {card["id"]: card for card in NativeDashboardService(tmp_path).snapshot().to_dict()["cards"]}

    assert "governance" in cards
    assert "open_approvals" in cards["governance"]["value"]
    assert "open_items" in cards["governance"]["value"]
    # Headline card must not expose technical ids.
    assert "approval_id" not in json.dumps(cards["governance"], ensure_ascii=False)


def test_trends_expose_7_and_30_day_windows(tmp_path):
    ReviewQueue(tmp_path).create(category="failed_import", title="I", source="c")

    result = ReviewApprovalMetrics(tmp_path).compute()

    assert set(result.trends.keys()) == {"7d", "30d"}
    assert result.trends["7d"]["created"] == 1
