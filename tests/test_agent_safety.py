from __future__ import annotations

import json

from secondbrain.agent.safety import ApprovalRequest, SafetyService
from secondbrain.agent.safety.audit import ApprovalAudit
from secondbrain.agent.safety.cli import main as approval_cli
from secondbrain.native.approval import (
    ApprovalRequest as NativeApprovalRequest,
    NativeActionAuditLog,
    NativeApprovalQueue,
    audit_path,
)


def test_safety_reexports_the_canonical_request_type():
    # The safety layer must not define a second ApprovalRequest schema.
    assert ApprovalRequest is NativeApprovalRequest


def test_native_queue_create_is_backward_compatible(tmp_path):
    # Pre-v30.61 call shape (no risk_level/reason) keeps the legacy defaults.
    legacy = NativeApprovalQueue(tmp_path).create(command="c", intent="i", text="t")
    assert legacy["risk_level"] == "write"
    assert legacy["status"] == "pending"
    # New call shape enriches the same record type.
    enriched = NativeApprovalQueue(tmp_path).create(
        command="c", intent="i", text="t", risk_level="destructive", reason="danger"
    )
    assert enriched["risk_level"] == "destructive"
    assert enriched["reason"] == "danger"


def test_end_to_end_request_lands_in_shared_audit_trail(tmp_path):
    service = SafetyService(tmp_path)
    record = service.request(actor="agent", action="email.send", text="mail")

    # audit trail is the shared native one
    assert service.audit.path == audit_path(tmp_path)
    events = service.audit_events(limit=10)
    assert len(events) == 1
    assert events[0]["intent"] == "safety.request"
    assert events[0]["target"] == record["approval_id"]
    assert "by agent" in events[0]["text"]


def test_full_lifecycle_request_approve_audit(tmp_path):
    service = SafetyService(tmp_path)
    record = service.request(actor="agent", action="file.write", text="edit")
    service.approve(record["approval_id"], decided_by="markus")

    events = service.audit_events(limit=10)
    intents = [e["intent"] for e in events]
    assert "safety.request" in intents
    assert "safety.approve" in intents


def test_policy_check_returns_level_and_verdict(tmp_path):
    service = SafetyService(tmp_path)
    level, verdict = service.policy_check("shell.exec")
    assert level == "destructive"
    assert verdict.requires_approval is True


def test_audit_only_returns_safety_events_by_default(tmp_path):
    # Write a non-safety native audit event, then a safety one.
    NativeActionAuditLog(tmp_path).append({"command": "noise", "intent": "other", "status": "x"})
    audit = ApprovalAudit(tmp_path)
    audit.write(actor="agent", action="file.write", event="request", outcome="pending",
                approval_id="abc", risk_level="medium", requires_approval=True)
    safety_only = audit.events(limit=10)
    assert all(e["intent"].startswith("safety.") for e in safety_only)
    mixed = audit.events(limit=10, safety_only=False)
    assert any(e.get("intent") == "other" for e in mixed)


def test_cli_list_show_approve_reject(tmp_path, capsys):
    root = str(tmp_path)
    service = SafetyService(tmp_path)
    rec = service.request(actor="agent", action="file.delete", text="rm", target="t")

    assert approval_cli(["approval-list", "--project-root", root]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["count"] == 1

    assert approval_cli(["approval-show", rec["approval_id"], "--project-root", root]) == 0
    shown = json.loads(capsys.readouterr().out)
    assert shown["approval"]["approval_id"] == rec["approval_id"]

    assert approval_cli(["approval-approve", rec["approval_id"], "--project-root", root, "--by", "markus"]) == 0
    approved = json.loads(capsys.readouterr().out)
    assert approved["status"] == "approved"

    # a second approval to reject
    rec2 = service.request(actor="agent", action="file.delete", text="rm2", target="t2")
    assert approval_cli(["approval-reject", rec2["approval_id"], "--project-root", root]) == 0
    rejected = json.loads(capsys.readouterr().out)
    assert rejected["status"] == "rejected"


def test_cli_show_missing_id_returns_error(tmp_path, capsys):
    assert approval_cli(["approval-show", "--project-root", str(tmp_path)]) == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is False


def test_cli_audit_command(tmp_path, capsys):
    root = str(tmp_path)
    SafetyService(tmp_path).request(actor="agent", action="api.external", text="call")
    assert approval_cli(["approval-audit", "--project-root", root]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["count"] >= 1
