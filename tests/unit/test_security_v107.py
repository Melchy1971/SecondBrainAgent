from pathlib import Path
from secondbrain.security_v107 import PolicyEngine, SecureCommandGateway, contains_secret, sanitize_payload
from secondbrain.secure_agent_kernel_v107 import SecureAgentKernel


def test_secret_detection_and_redaction():
    assert contains_secret("api_key=sk-1234567890abcdef")
    assert "sk-123" not in sanitize_payload({"api_key": "sk-1234567890abcdef"})["api_key"]


def test_safe_write_is_allowed(tmp_path):
    gw = SecureCommandGateway(tmp_path, PolicyEngine(max_level=2))
    gw.register("note.create", lambda p: {"ok": p["title"]}, level="write")
    result = gw.execute("note.create", {"title": "Test"})
    assert result["ok"] is True
    assert result["result"]["ok"] == "Test"


def test_execute_requires_or_blocks(tmp_path):
    gw = SecureCommandGateway(tmp_path, PolicyEngine(max_level=2))
    gw.register("system.shell", lambda p: {"executed": True}, level="execute")
    result = gw.execute("system.shell", {"cmd": "echo hi"})
    assert result["ok"] is False
    assert result["reason"] in {"level_exceeds_policy", "approval_required", "risk_blocked"}


def test_high_risk_write_creates_approval(tmp_path):
    gw = SecureCommandGateway(tmp_path, PolicyEngine(max_level=2, approval_threshold=60, block_threshold=100))
    gw.register("email.send", lambda p: {"sent": True}, level="write")
    result = gw.execute("email.send", {"to": "a@example.com", "body": "hello"})
    assert result["ok"] is False
    assert result["reason"] == "approval_required"
    assert result["approval_id"]
    assert len(gw.approvals.pending()) == 1


def test_approved_high_risk_write_executes(tmp_path):
    gw = SecureCommandGateway(tmp_path, PolicyEngine(max_level=2, approval_threshold=60, block_threshold=100))
    gw.register("email.send", lambda p: {"sent": p["to"]}, level="write")
    first = gw.execute("email.send", {"to": "a@example.com", "body": "hello"})
    gw.approvals.approve(first["approval_id"])
    second = gw.execute("email.send", {"to": "a@example.com", "body": "hello", "approval_id": first["approval_id"]})
    assert second["ok"] is True
    assert second["result"]["sent"] == "a@example.com"


def test_audit_log_redacts_secrets(tmp_path):
    gw = SecureCommandGateway(tmp_path, PolicyEngine(max_level=2))
    gw.register("note.create", lambda p: {"created": True}, level="write")
    gw.execute("note.create", {"title": "x", "api_key": "sk-1234567890abcdef"})
    raw = (tmp_path / "audit_v107.jsonl").read_text(encoding="utf-8")
    assert "sk-1234567890abcdef" not in raw
    assert "***REDACTED***" in raw


def test_secure_agent_kernel_blocks_unapproved_external_action(tmp_path):
    kernel = SecureAgentKernel(tmp_path, PolicyEngine(max_level=2, approval_threshold=60, block_threshold=100))
    kernel.register_handler("email.send", lambda p: {"sent": True}, level="write")
    kernel.submit("email.send", {"to": "a@example.com", "body": "hi"})
    result = kernel.tick()
    assert result["blocked"] == 1
    assert kernel.approvals_v107.pending()
