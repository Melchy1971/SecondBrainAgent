from datetime import datetime, timezone

from secondbrain.desktop_native.approval_surface import ApprovalSurface, approval_activity
from secondbrain.native.approval import NativeApprovalQueue


def _create(queue, workspace, recipient):
    return queue.create(
        command="mail.send",
        intent="mail.send",
        text="",
        target="mail",
        risk_level="external_write",
        reason="native_action_policy",
        payload={"recipient": recipient, "body": "vertraulicher Inhalt", "binding": "secret-binding"},
        workspace_id=workspace,
    )


def test_surface_filters_pending_approvals_by_exact_workspace(tmp_path):
    queue = NativeApprovalQueue(tmp_path)
    own = _create(queue, "alpha", "own@example.test")
    _create(queue, "beta", "other@example.test")
    snapshot = ApprovalSurface(queue, workspace_id="alpha").snapshot()
    assert snapshot["pending_count"] == 1
    assert snapshot["items"][0]["approval_id"] == own["approval_id"]
    assert snapshot["workspace_isolated"] is True


def test_surface_never_exposes_payload_text_or_workspace_identifier(tmp_path):
    queue = NativeApprovalQueue(tmp_path)
    _create(queue, "alpha", "secret@example.test")
    snapshot = ApprovalSurface(queue, workspace_id="alpha").snapshot()
    rendered = repr(snapshot)
    assert "secret@example.test" not in rendered
    assert "vertraulicher Inhalt" not in rendered
    assert "secret-binding" not in rendered
    assert "workspace_id" not in rendered
    assert snapshot["payloads_exposed"] is False


def test_surface_excludes_non_pending_and_limits_visible_rows(tmp_path):
    queue = NativeApprovalQueue(tmp_path)
    first = _create(queue, "alpha", "first@example.test")
    queue.reject(first["approval_id"], actor="tester")
    _create(queue, "alpha", "second@example.test")
    _create(queue, "alpha", "third@example.test")
    snapshot = ApprovalSurface(queue, workspace_id="alpha", limit=1).snapshot()
    assert snapshot["pending_count"] == 2
    assert snapshot["visible_count"] == 1


def test_approval_activity_counts_elevated_visible_items_without_payloads():
    result = approval_activity(
        {
            "pending_count": 3,
            "items": [
                {"risk_level": "external_write", "payload": "secret"},
                {"risk_level": "destructive"},
                {"risk_level": "read_only"},
            ],
        }
    )
    assert result == {
        "available": True,
        "pending": 3,
        "elevated": 2,
        "overdue": 0,
        "severity": "warning",
        "label": "3 Pending / 2 Elevated",
    }
    assert "secret" not in str(result)


def test_approval_activity_normalizes_invalid_snapshot():
    assert approval_activity({"pending_count": "invalid", "items": "invalid"}) == {
        "available": False,
        "pending": 0,
        "elevated": 0,
        "overdue": 0,
        "severity": "unavailable",
        "label": "Unavailable",
    }


def test_approval_activity_marks_visible_items_overdue_after_fifteen_minutes():
    result = approval_activity(
        {
            "pending_count": 3,
            "items": [
                {"created_at": "2026-07-20T09:44:59Z"},
                {"created_at": "2026-07-20T09:45:00+00:00"},
                {"created_at": "invalid"},
            ],
        },
        now=datetime(2026, 7, 20, 10, 0, tzinfo=timezone.utc),
    )
    assert result == {
        "available": True,
        "pending": 3,
        "elevated": 0,
        "overdue": 2,
        "severity": "critical",
        "label": "3 Pending / 2 Overdue",
    }


def test_approval_activity_marks_empty_queue_as_normal():
    result = approval_activity({"pending_count": 0, "items": []})
    assert result["severity"] == "normal"
