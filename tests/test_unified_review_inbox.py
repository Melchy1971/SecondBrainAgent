from __future__ import annotations

import pytest

from secondbrain.agent.approval_bridge import AgentApprovalBridge
from secondbrain.agent.review_service import UnifiedReviewInbox
from secondbrain.agent.tool_registry import ToolDefinition, ToolRiskLevel
from secondbrain.native.approval import NativeApprovalQueue, ReviewQueue
from secondbrain.native.runtime_snapshot import build_native_view_model


def _linked_item(tmp_path, *, category: str = "delete_request"):
    approvals = NativeApprovalQueue(tmp_path)
    reviews = ReviewQueue(tmp_path)
    bridge = AgentApprovalBridge(queue=approvals, review_queue=reviews)
    tool = ToolDefinition(
        "records.delete",
        "Delete record",
        risk_level=ToolRiskLevel.HIGH,
        handler=lambda payload: None,
    )
    approval = bridge.create_approval(
        plan_id="plan-1",
        step_id="step-1",
        tool=tool,
        intent="delete_record",
        payload={"record_id": "1"},
        create_review=True,
        review_title="Delete record 1",
        review_description="Destructive action",
        review_source="agent",
        review_category=category,
    )
    review = reviews.get(approval["review_id"])
    assert review is not None
    return approvals, reviews, approval, review


def test_review_and_approval_appear_in_one_inbox(tmp_path):
    approvals = NativeApprovalQueue(tmp_path)
    reviews = ReviewQueue(tmp_path)
    approval = approvals.create(command="external.write", intent="write", text="Write externally")
    review = reviews.create(
        category="failed_import",
        title="Import failed",
        description="Retry or dismiss",
        source="importer",
    )

    items = UnifiedReviewInbox(approval_queue=approvals, review_queue=reviews).list_all()

    assert {item["item_id"] for item in items} == {approval["approval_id"], review["review_id"]}
    assert {item["item_type"] for item in items} == {"approval", "review"}
    expected_fields = {
        "item_id",
        "item_type",
        "category",
        "status",
        "title",
        "description",
        "source",
        "target",
        "risk_level",
        "plan_id",
        "step_id",
        "created_at",
        "updated_at",
        "actions_allowed",
    }
    assert set(items[0]) == expected_fields


def test_linked_review_and_approval_are_not_duplicated(tmp_path):
    approvals, reviews, approval, review = _linked_item(tmp_path)
    inbox = UnifiedReviewInbox(approval_queue=approvals, review_queue=reviews)

    items = inbox.list_all()

    assert len(items) == 1
    assert items[0]["item_id"] == approval["approval_id"]
    assert items[0]["item_type"] == "approval"
    assert items[0]["title"] == "Delete record 1"
    assert inbox.get(review["review_id"])["item_id"] == approval["approval_id"]


@pytest.mark.parametrize(
    ("decision", "expected_status"),
    [("approve", "approved"), ("reject", "rejected"), ("defer", "deferred")],
)
def test_decision_updates_linked_approval_and_review(tmp_path, decision, expected_status):
    approvals, reviews, approval, review = _linked_item(tmp_path)
    inbox = UnifiedReviewInbox(approval_queue=approvals, review_queue=reviews)

    if decision == "defer":
        result = inbox.defer(
            approval["approval_id"],
            "reviewer",
            until="2026-07-15T09:00:00+00:00",
            note="later",
        )
    else:
        result = getattr(inbox, decision)(approval["approval_id"], "reviewer", "decision note")

    stored_approval = approvals.get(approval["approval_id"])
    stored_review = reviews.get(review["review_id"])
    assert result["status"] == expected_status
    assert stored_approval["status"] == expected_status
    assert stored_review["status"] == expected_status
    assert stored_approval["decision_audit"]
    assert stored_review["decision_audit"]
    if expected_status == "deferred":
        assert stored_approval["deferred_until"] == "2026-07-15T09:00:00+00:00"
        assert stored_review["deferred_until"] == "2026-07-15T09:00:00+00:00"
        assert inbox.list_deferred()[0]["item_id"] == approval["approval_id"]
    else:
        assert inbox.list_completed()[0]["item_id"] == approval["approval_id"]


def test_runtime_snapshot_contains_unified_inbox_totals(tmp_path):
    approvals, reviews, _, _ = _linked_item(tmp_path)
    reviews.create(category="failed_import", title="Import failed", source="importer")
    deferred = approvals.create(
        command="custom.write",
        intent="write",
        text="Custom write",
        risk_level="critical",
    )
    approvals.transition(deferred["approval_id"], "deferred", actor="reviewer")

    snapshot = build_native_view_model(tmp_path)

    assert snapshot["pending_reviews"] == 2
    assert snapshot["pending_approvals"] == 1
    assert snapshot["deferred_items"] == 1
    assert snapshot["critical_items"] == 2
    assert snapshot["inbox_summary"]["total"] == 3
    assert snapshot["inbox_summary"]["pending"] == 2


def test_category_filter_and_critical_sorting(tmp_path):
    reviews = ReviewQueue(tmp_path)
    reviews.create(category="failed_import", title="Old import", source="importer")
    reviews.create(category="sensitive_document", title="Sensitive", source="classifier")
    inbox = UnifiedReviewInbox(review_queue=reviews, approval_queue=NativeApprovalQueue(tmp_path))

    all_items = inbox.list_pending()
    sensitive = inbox.list_pending(category="sensitive_document")

    assert all_items[0]["category"] == "sensitive_document"
    assert [item["title"] for item in sensitive] == ["Sensitive"]
    assert sensitive[0]["actions_allowed"] == ["approve", "reject", "defer"]
