"""Prompt 12 - notifications and escalation for pending review/approval items.

Acceptance coverage:
  1. A new risky approval produces a notification.
  2. Delete request gets high priority.
  3. Credential change gets critical priority.
  4. An overdue item escalates.
  5. Snooze suppresses until it expires.
  6. Acknowledgement is persisted.
  7. No duplicate notification.
  8. Notifications contain no secrets.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

from secondbrain.agent.review_service import UnifiedReviewInbox
from secondbrain.gui.approval_inbox import ApprovalInboxViewModel
from secondbrain.native.approval import NativeApprovalQueue, ReviewQueue
from secondbrain.native.notification_center.service import NotificationCenterService
from secondbrain.native.runtime_snapshot import build_native_view_model
from secondbrain.notifications.review_notifications import (
    NotificationPriority,
    NotificationType,
    ReviewNotificationService,
    TimeRules,
    priority_for,
)

NOW = datetime(2026, 7, 13, 12, 0, 0, tzinfo=timezone.utc)


def _item(**kwargs):
    base = {
        "item_id": "i1",
        "item_type": "approval",
        "category": "",
        "status": "pending",
        "risk_level": "write",
        "created_at": NOW.isoformat(),
        "title": "Aktion",
        "deferred_until": "",
        "change_type": "",
    }
    base.update(kwargs)
    return base


def _service(tmp_path, **rules):
    time_rules = TimeRules(**rules) if rules else TimeRules()
    return ReviewNotificationService(time_rules=time_rules, state_path=tmp_path / "notif_state.json")


# -- 1 + 2 -----------------------------------------------------------------

def test_new_risky_approval_creates_notification(tmp_path):
    approvals = NativeApprovalQueue(tmp_path)
    approvals.create(command="records.delete", intent="delete_record", text="Delete 1", category="delete_request", risk_level="high")
    inbox = UnifiedReviewInbox(tmp_path)

    notifications = inbox.evaluate_notifications(now=datetime.now(timezone.utc))

    assert len(notifications) == 1
    assert notifications[0].type is NotificationType.APPROVAL_REQUESTED
    assert notifications[0].priority is NotificationPriority.HIGH


def test_delete_request_gets_high_priority():
    service = ReviewNotificationService()
    [notification] = service.evaluate([_item(category="delete_request")], now=NOW)
    assert notification.priority is NotificationPriority.HIGH


# -- 3 ---------------------------------------------------------------------

def test_credential_change_gets_critical():
    assert priority_for(change_type="credential_change") is NotificationPriority.CRITICAL
    service = ReviewNotificationService()
    [notification] = service.evaluate([_item(category="credential_change")], now=NOW)
    assert notification.priority is NotificationPriority.CRITICAL
    assert notification.type is NotificationType.CRITICAL_APPROVAL_REQUESTED
    assert notification.system_critical is True


# -- 4 ---------------------------------------------------------------------

def test_overdue_item_escalates(tmp_path):
    service = _service(tmp_path, overdue_after=timedelta(hours=4), escalation_interval=timedelta(hours=1))
    created = (NOW - timedelta(hours=6)).isoformat()
    item = _item(item_id="r1", item_type="review", category="failed_import", created_at=created)

    [notification] = service.evaluate([item], now=NOW)

    assert notification.type is NotificationType.REVIEW_OVERDUE
    # failed_import is normally "normal", but overdue escalates to at least high.
    assert notification.priority is NotificationPriority.HIGH


# -- 5 ---------------------------------------------------------------------

def test_snooze_suppresses_until_expiry(tmp_path):
    service = _service(tmp_path, escalation_interval=timedelta(minutes=30))
    item = _item(category="sensitive_document", item_type="review")

    [first] = service.evaluate([item], now=NOW)
    service.snooze(first.dedup_key, NOW + timedelta(hours=5))

    assert service.evaluate([item], now=NOW + timedelta(minutes=15)) == []
    # Snooze applies to the item, including a newly derived overdue escalation.
    assert service.evaluate([item], now=NOW + timedelta(hours=4, minutes=30)) == []
    later = service.evaluate([item], now=NOW + timedelta(hours=6))
    assert len(later) == 1
    assert later[0].type is NotificationType.REVIEW_OVERDUE


# -- 6 ---------------------------------------------------------------------

def test_acknowledgement_is_persisted(tmp_path):
    service = _service(tmp_path)
    item = _item(category="sensitive_document", item_type="review")
    [notification] = service.evaluate([item], now=NOW)

    service.acknowledge(notification.dedup_key)

    # New instance backed by the same state file still sees the ack.
    reloaded = ReviewNotificationService(state_path=tmp_path / "notif_state.json")
    assert reloaded.is_acknowledged(notification.dedup_key)
    assert reloaded.evaluate([item], now=NOW + timedelta(hours=2)) == []


# -- 7 ---------------------------------------------------------------------

def test_no_duplicate_within_cooldown(tmp_path):
    service = _service(tmp_path, escalation_interval=timedelta(hours=1))
    item = _item(category="delete_request")

    first = service.evaluate([item], now=NOW)
    second = service.evaluate([item], now=NOW + timedelta(minutes=10))

    assert len(first) == 1
    assert second == []


def test_desktop_bridge_deduplicates(tmp_path):
    approvals = NativeApprovalQueue(tmp_path)
    approvals.create(command="records.delete", intent="delete", text="Del", category="delete_request", risk_level="high")
    inbox = UnifiedReviewInbox(tmp_path)
    center = NotificationCenterService(tmp_path)
    notifications = inbox.evaluate_notifications(now=NOW)

    first = center.push_review_notifications(notifications)
    second = center.push_review_notifications(notifications)

    assert first["pushed"] == 1
    assert second["pushed"] == 0
    assert center.review_badge() == 1


# -- 8 ---------------------------------------------------------------------

def test_notifications_contain_no_secrets(tmp_path):
    service = _service(tmp_path)
    secret = "hunter2_TOP_SECRET"
    item = _item(category="sensitive_document", item_type="review", title=f"password={secret}")

    [notification] = service.evaluate([item], now=NOW)

    dumped = json.dumps(notification.to_dict(), ensure_ascii=False)
    assert secret not in dumped
    assert "password=" not in dumped
    assert "[REDACTED_SECRET]" in notification.title


# -- additional notification types ----------------------------------------

def test_deferred_item_due(tmp_path):
    service = _service(tmp_path)
    due = (NOW - timedelta(minutes=5)).isoformat()
    item = _item(item_id="d1", item_type="review", category="failed_import", status="deferred", deferred_until=due)

    [notification] = service.evaluate([item], now=NOW)

    assert notification.type is NotificationType.DEFERRED_DUE


def test_deferred_item_not_yet_due_is_silent(tmp_path):
    service = _service(tmp_path)
    due = (NOW + timedelta(hours=2)).isoformat()
    item = _item(item_type="review", status="deferred", deferred_until=due)

    assert service.evaluate([item], now=NOW) == []


def test_approval_expiring_and_expired(tmp_path):
    service = _service(tmp_path, approval_expiration=timedelta(hours=24), expiring_window=timedelta(hours=2))

    expiring = _item(item_id="e1", created_at=(NOW - timedelta(hours=23)).isoformat())
    [n_expiring] = service.evaluate([expiring], now=NOW)
    assert n_expiring.type is NotificationType.APPROVAL_EXPIRING

    expired = _item(item_id="e2", created_at=(NOW - timedelta(hours=30)).isoformat())
    [n_expired] = service.evaluate([expired], now=NOW)
    assert n_expired.type is NotificationType.APPROVAL_EXPIRED


def test_decision_recorded_event(tmp_path):
    service = _service(tmp_path)
    view = {"item_id": "x1", "item_type": "approval", "category": "delete_request", "title": "Del"}

    notification = service.record_decision(view, "approved", now=NOW)

    assert notification.type is NotificationType.DECISION_RECORDED
    assert notification.metadata["status"] == "approved"


def test_runtime_snapshot_exposes_notification_metrics(tmp_path):
    NativeApprovalQueue(tmp_path).create(command="records.delete", intent="delete", text="Del", category="delete_request", risk_level="high")
    ReviewQueue(tmp_path).create(category="failed_import", title="Import", source="imp")

    snapshot = build_native_view_model(tmp_path)

    for key in ("open_items", "overdue_items", "critical_items", "expiring_items", "notification_count", "oldest_pending_age"):
        assert key in snapshot
    assert snapshot["open_items"] == 2
    assert snapshot["notification_count"] == 2


def test_badge_counts_high_and_critical_only(tmp_path):
    service = _service(tmp_path)
    items = [
        _item(item_id="a", category="delete_request"),          # high
        _item(item_id="b", category="credential_change"),        # critical
        _item(item_id="c", item_type="review", category="failed_import"),  # normal
    ]

    assert service.badge_count(items, now=NOW) == 2


def test_notification_lifecycle_create_list_acknowledge_snooze_and_dismiss(tmp_path):
    service = _service(tmp_path)
    created = service.create(_item(item_id="created", category="delete_request"), now=NOW)

    assert service.list_open(now=NOW) == [created]
    service.snooze(created.id, NOW + timedelta(hours=1))
    assert service.list_open(now=NOW + timedelta(minutes=30)) == []
    assert service.list_open(now=NOW + timedelta(hours=2)) == [created]
    service.acknowledge(created.id, now=NOW + timedelta(hours=2))
    assert service.list_open(now=NOW + timedelta(hours=3)) == []

    dismissed = service.create(_item(item_id="dismissed", category="failed_import"), now=NOW)
    service.dismiss(dismissed.id, now=NOW)
    assert dismissed not in service.list_open(now=NOW)


def test_recovery_required_is_critical_and_overdue(tmp_path):
    service = _service(tmp_path)
    [notification] = service.evaluate(
        [_item(item_id="recover", status="recovery_required", risk_level="low")],
        now=NOW,
    )

    assert notification.type is NotificationType.RECOVERY_REQUIRED
    assert notification.priority is NotificationPriority.CRITICAL
    assert notification.system_critical is True
    assert service.list_overdue(now=NOW) == [notification]


def test_crashed_approval_emits_recovery_notification(tmp_path):
    now = datetime.now(timezone.utc)
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
    queue.recover_stale_leases(now=now + timedelta(days=1))

    [notification] = UnifiedReviewInbox(tmp_path).evaluate_notifications(now=now + timedelta(days=1))

    assert notification.type is NotificationType.RECOVERY_REQUIRED
    assert notification.priority is NotificationPriority.CRITICAL


def test_deep_link_opens_exact_inbox_item(tmp_path):
    approval = NativeApprovalQueue(tmp_path).create(
        command="records.delete",
        intent="delete",
        text="Delete",
        category="delete_request",
        risk_level="high",
    )
    view_model = ApprovalInboxViewModel(tmp_path)

    link = view_model.deep_link(approval["approval_id"])
    detail = view_model.open_deep_link(link)

    assert link == f"secondbrain://inbox/{approval['approval_id']}"
    assert detail["item_id"] == approval["approval_id"]


def test_persistent_notification_state_contains_no_secret(tmp_path):
    service = _service(tmp_path)
    secret = "sk-super-secret-value"
    service.create(
        _item(item_id="safe-id", item_type="review", title=f"password={secret}"),
        now=NOW,
    )

    stored = (tmp_path / "notif_state.json").read_text(encoding="utf-8")
    assert secret not in stored
    assert "password=" not in stored


def test_runtime_snapshot_exposes_notification_counters(tmp_path):
    NativeApprovalQueue(tmp_path).create(
        command="credentials.rotate",
        intent="credential_change",
        text="Rotate credentials",
        category="connector_permission_change",
        risk_level="critical",
    )

    snapshot = build_native_view_model(tmp_path)

    assert snapshot["open_notifications"] == 1
    assert snapshot["critical_notifications"] == 1
    assert snapshot["overdue_notifications"] == 0
    assert snapshot["expiring_approvals"] == 0
    assert snapshot["oldest_pending_age"] >= 0
