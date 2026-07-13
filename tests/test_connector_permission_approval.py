from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest

from secondbrain.agent.approval_service import AgentApprovalService
from secondbrain.connectors.scaffold.approval import (
    ApprovalBindingMismatch,
    ApprovalConflict,
    ApprovalExpired,
    ApprovalGate,
    ApprovalRequired,
    ConnectorActionPolicy,
)
from secondbrain.connectors.scaffold.oauth2 import OAuth2Authenticator, OAuth2Config
from secondbrain.connectors.scaffold.transport import FakeTransport
from secondbrain.connectors.token_repository import TokenRepository
from secondbrain.desktop.connectors import ConnectorCenterService, ConnectorDescriptor
from secondbrain.native.approval import approval_path


def _gate(tmp_path, *, clock=None, workspace_id="workspace-1", scopes=("mail.read",)):
    state = clock or {"now": 1_000.0}
    service = AgentApprovalService(tmp_path)
    gate = ApprovalGate(
        approval_service=service,
        connector_id="gmail",
        workspace_id=workspace_id,
        actor="alice",
        effective_scopes=scopes,
        approval_ttl_seconds=60,
        clock=lambda: state["now"],
    )
    return gate, service, state


def _request(gate: ApprovalGate, **overrides):
    values = {
        "action": "gmail.send",
        "resource": "gmail",
        "method": "POST",
        "target": "recipient@example.com",
        "payload": {"subject": "Hello", "recipient_count": 1},
        "execute": lambda: "sent",
    }
    values.update(overrides)
    with pytest.raises(ApprovalRequired) as raised:
        gate.guard(**values)
    return raised.value.request, values


def test_read_only_sync_within_effective_scopes_runs_without_approval(tmp_path) -> None:
    gate, service, _ = _gate(tmp_path)
    calls = []

    result = gate.guard(
        action="connector.sync",
        resource="gmail",
        method="GET",
        target="inbox",
        payload={"mode": "delta"},
        requested_scopes=("mail.read",),
        execute=lambda: calls.append("sync") or "ok",
    )

    assert result == "ok"
    assert calls == ["sync"]
    assert service.list_pending() == []


def test_scope_comparison_without_diff_runs_without_approval() -> None:
    decision = ConnectorActionPolicy().evaluate(
        connector_id="gmail",
        action="oauth.scope.update",
        method="GET",
        effective_scopes=("mail.read",),
        requested_scopes=("mail.read",),
    )

    assert decision.added_scopes == ()
    assert decision.requires_approval is False
    assert decision.policy_rule == "read_only"


def test_explicit_read_label_cannot_downgrade_a_write() -> None:
    policy = ConnectorActionPolicy()

    named_write = policy.evaluate(
        connector_id="gmail",
        action="gmail.send",
        method="GET",
        action_type="read",
    )
    mutating_method = policy.evaluate(
        connector_id="custom",
        action="custom.health",
        method="POST",
        action_type="read",
    )

    assert named_write.action_type == "send"
    assert named_write.requires_approval is True
    assert mutating_method.action_type == "update"
    assert mutating_method.requires_approval is True


def test_scope_expansion_is_blocked_with_complete_scope_diff(tmp_path) -> None:
    gate, service, _ = _gate(tmp_path)

    with pytest.raises(ApprovalRequired) as raised:
        gate.guard(
            action="oauth.scope.update",
            resource="gmail",
            method="GET",
            target="oauth",
            payload={"reason": "enable send"},
            requested_scopes=("mail.read", "mail.send"),
            execute=lambda: "changed",
        )

    request = raised.value.request
    stored = service.get(request.request_id)
    assert request.effective_scopes == ("mail.read",)
    assert request.requested_scopes == ("mail.read", "mail.send")
    assert request.added_scopes == ("mail.send",)
    assert request.removed_scopes == ()
    assert request.requires_approval is True
    assert request.approval_category == "connector_permission_change"
    assert stored["category"] == "connector_permission_change"


def test_email_send_is_blocked_and_payload_is_only_persisted_as_hash(tmp_path) -> None:
    gate, service, _ = _gate(tmp_path)
    secret = "mail-secret-value"

    request, _ = _request(gate, payload={"subject": "Hello", "token": secret})

    stored = service.get(request.request_id)
    assert stored["status"] == "pending"
    assert stored["category"] == "risky_agent_action"
    assert stored["payload"]["action_type"] == "send"
    assert stored["payload"]["payload_hash"]
    assert stored["payload"]["idempotency_key"]
    assert secret not in approval_path(tmp_path).read_text(encoding="utf-8")


def test_file_upload_is_blocked_as_risky_agent_action(tmp_path) -> None:
    gate, service, _ = _gate(tmp_path, scopes=("files.read",))

    request, _ = _request(
        gate,
        action="drive.file.upload",
        resource="drive",
        target="external-folder",
        payload={"name": "report.pdf", "content_hash": "sha256:document"},
    )

    stored = service.get(request.request_id)
    assert request.action_type == "upload"
    assert stored["category"] == "risky_agent_action"


def test_external_delete_uses_delete_request_category(tmp_path) -> None:
    gate, service, _ = _gate(tmp_path)

    request, _ = _request(
        gate,
        action="calendar.event.delete",
        resource="calendar",
        method="DELETE",
        target="event-42",
        payload={"event_id": "event-42"},
    )

    assert request.action_type == "delete"
    assert service.get(request.request_id)["category"] == "delete_request"


def test_delete_http_method_cannot_hide_behind_generic_action_name() -> None:
    decision = ConnectorActionPolicy().evaluate(
        connector_id="calendar",
        action="calendar.event",
        method="DELETE",
    )

    assert decision.action_type == "delete"
    assert decision.requires_approval is True
    assert decision.approval_category == "delete_request"


def test_confirmed_boolean_does_not_replace_persistent_approval(tmp_path) -> None:
    gate, service, _ = _gate(tmp_path)
    calls = []

    with pytest.raises(ApprovalRequired):
        gate.guard(
            action="gmail.send",
            resource="gmail",
            method="POST",
            target="recipient@example.com",
            payload={"subject": "Hello"},
            confirmed=True,
            execute=lambda: calls.append("sent"),
        )

    assert calls == []
    assert len(service.list_pending()) == 1


def test_approved_scope_change_executes_exactly_once(tmp_path) -> None:
    gate, service, _ = _gate(tmp_path)
    calls = []
    kwargs = {
        "action": "oauth.scope.update",
        "resource": "gmail",
        "method": "POST",
        "target": "oauth",
        "payload": {"requested": ["mail.read", "mail.send"]},
        "requested_scopes": ("mail.read", "mail.send"),
        "execute": lambda: calls.append("changed") or "changed",
    }
    with pytest.raises(ApprovalRequired) as raised:
        gate.guard(**kwargs)
    approval_id = raised.value.request.request_id
    gate.approve(approval_id, actor="reviewer")

    assert gate.guard(**kwargs) == "changed"
    with pytest.raises(ApprovalConflict, match="already_consumed"):
        gate.guard(**kwargs)

    assert calls == ["changed"]
    assert service.get(approval_id)["status"] == "executed"


def test_parallel_consumers_execute_approved_action_once(tmp_path) -> None:
    gate, _, _ = _gate(tmp_path)
    calls = []
    request, values = _request(gate, execute=lambda: calls.append("sent") or "sent")
    gate.approve(request.request_id, actor="reviewer")
    start = Barrier(2)

    def consume() -> str:
        start.wait()
        try:
            return gate.guard(**values, approval_id=request.request_id)
        except ApprovalConflict:
            return "conflict"

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: consume(), range(2)))

    assert sorted(results) == ["conflict", "sent"]
    assert calls == ["sent"]


def test_changed_payload_invalidates_existing_approval(tmp_path) -> None:
    gate, _, _ = _gate(tmp_path)
    request, values = _request(gate)
    gate.approve(request.request_id, actor="reviewer")

    with pytest.raises(ApprovalBindingMismatch, match="binding_mismatch"):
        gate.guard(
            **{
                **values,
                "payload": {"subject": "Changed", "recipient_count": 1},
                "approval_id": request.request_id,
            }
        )


def test_expired_approval_is_rejected_without_execution(tmp_path) -> None:
    gate, _, clock = _gate(tmp_path)
    calls = []
    request, values = _request(gate, execute=lambda: calls.append("sent"))
    gate.approve(request.request_id, actor="reviewer")
    clock["now"] += 61

    with pytest.raises(ApprovalExpired, match="expired"):
        gate.guard(**values, approval_id=request.request_id)

    assert calls == []


def test_workspace_change_invalidates_existing_approval(tmp_path) -> None:
    gate, _, _ = _gate(tmp_path, workspace_id="workspace-1")
    request, values = _request(gate)
    gate.approve(request.request_id, actor="reviewer")

    with pytest.raises(ApprovalBindingMismatch, match="binding_mismatch"):
        gate.guard(**values, workspace_id="workspace-2", approval_id=request.request_id)


def test_decision_and_execution_are_present_in_native_audit(tmp_path) -> None:
    gate, service, _ = _gate(tmp_path)
    request, values = _request(gate)
    gate.approve(request.request_id, actor="security-reviewer")
    gate.guard(**values)

    stored = service.get(request.request_id)
    transitions = [(row["new_status"], row["actor"]) for row in stored["decision_audit"]]
    assert transitions == [
        ("approved", "security-reviewer"),
        ("executing", "connector_executor"),
        ("executed", "connector_executor"),
    ]
    assert stored["payload"]["connector_id"] == "gmail"
    assert stored["payload"]["workspace_id"] == "workspace-1"
    assert stored["payload"]["actor"] == "alice"
    execution_audit = stored["decision_audit"][-1]
    assert execution_audit["requested_action"] == "gmail.send"
    assert execution_audit["effective_action"] == "send"
    assert execution_audit["connector_id"] == "gmail"
    assert execution_audit["workspace_id"] == "workspace-1"
    assert execution_audit["scope_diff"] == {"added": [], "removed": []}
    assert execution_audit["payload_hash"] == stored["payload"]["payload_hash"]
    assert execution_audit["result"] == "executed"


def test_policy_covers_permission_and_connector_write_rules() -> None:
    policy = ConnectorActionPolicy()
    decision = policy.evaluate(
        connector_id="github",
        action="github.pull_request.create",
        method="POST",
        effective_scopes=("repo.read", "obsolete"),
        requested_scopes=("repo.read", "repo.write"),
        payload={"title": "PR"},
    )

    assert decision.added_scopes == ("repo.write",)
    assert decision.removed_scopes == ("obsolete",)
    assert decision.risk_level == "high"
    assert decision.requires_approval is True
    assert decision.approval_category == "connector_permission_change"
    assert decision.action_type == "permission_change"
    assert decision.existing_scopes == ("obsolete", "repo.read")
    assert "payload" not in json.dumps(decision.to_dict())


def test_connector_center_exposes_sanitized_permission_preview() -> None:
    center = ConnectorCenterService()
    center.register_connector(ConnectorDescriptor("gmail", "Gmail"))

    preview = center.permission_preview(
        "gmail",
        "oauth.scope.update",
        effective_scopes=("mail.read",),
        requested_scopes=("mail.read", "mail.send"),
        payload={"token": "must-not-appear"},
    )

    assert preview["effective_scopes"] == ["mail.read"]
    assert preview["added_scopes"] == ["mail.send"]
    assert preview["requires_approval"] is True
    assert preview["approval_category"] == "connector_permission_change"
    assert "must-not-appear" not in json.dumps(preview)


def test_oauth_scope_expansion_blocks_device_login_until_native_approval(tmp_path) -> None:
    token_repo = TokenRepository(str(tmp_path / "tokens.json"))
    token_repo.save("demo", {"access_token": "redacted", "scope": "scope.read"})
    transport = FakeTransport()
    transport.on("POST", "/device", lambda u, m, h, b: transport.json_response(200, {
        "device_code": "dc",
        "user_code": "uc",
        "verification_uri": "https://example.test/device",
        "expires_in": 900,
        "interval": 1,
    }))
    auth = OAuth2Authenticator(
        OAuth2Config(
            client_id="client",
            scopes=("scope.read", "scope.write"),
            token_url="https://example.test/token",
            devicecode_url="https://example.test/device",
            provider="demo",
            token_store_path=str(tmp_path / "tokens.json"),
        ),
        transport=transport,
        token_repo=token_repo,
    )

    with pytest.raises(ApprovalRequired):
        auth.begin_device_login()
    request = auth.scope_gate.pending()[0]
    auth.scope_gate.approve(request.request_id, actor="oauth-reviewer")

    started = auth.begin_device_login()
    assert started.device_code == "dc"
    assert len(transport.calls) == 1
