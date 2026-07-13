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
from secondbrain.native.approval import NativeApprovalQueue, ReviewQueue, review_path, approval_path
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


# -- 6 ---------------------------------------------------------------------

def test_export_contains_no_secrets_or_payloads(tmp_path):
    approvals = NativeApprovalQueue(tmp_path)
    approvals.create(
        command="connector.push",
        intent="send",
        text="Send data",
        category="external_send",
        payload={"password": "hunter2_TOP_SECRET", "body": "personal-content"},
    )

    export = ReviewApprovalMetrics(tmp_path).export()
    blob = json.dumps(export, ensure_ascii=False)

    assert "hunter2_TOP_SECRET" not in blob
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
    # Headline card must not expose technical ids.
    assert "approval_id" not in json.dumps(cards["governance"], ensure_ascii=False)


def test_trends_expose_7_and_30_day_windows(tmp_path):
    ReviewQueue(tmp_path).create(category="failed_import", title="I", source="c")

    result = ReviewApprovalMetrics(tmp_path).compute()

    assert set(result.trends.keys()) == {"7d", "30d"}
    assert result.trends["7d"]["created"] == 1
