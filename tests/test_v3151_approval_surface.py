from secondbrain.desktop_native.approval_surface import ApprovalSurface
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
