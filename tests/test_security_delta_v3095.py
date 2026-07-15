"""Regression tests for the v30.95 security delta guards (Prompt 34 Phase 2/4).

Each critical finding closed by ``security_delta_v3095`` has a positive and a
negative case here. These run without the full application runtime.
"""

from __future__ import annotations

import hmac
from hashlib import sha256

import pytest

from secondbrain.security_delta_v3095 import (
    ACTION_BLOCK, ReplayGuard, RiskLevel, TrustLevel, assert_same_workspace,
    classify_fetch_target, contains_shell_metacharacters, is_safe_redirect,
    resolve_within_root, run_security_delta_checks, safe_sql_identifier,
    sanitize_log_value, tabular_within_limits, verify_manifest_signature,
)


# Acceptance 4: private and internal network targets are controlled (SSRF)
@pytest.mark.parametrize("url", [
    "http://169.254.169.254/latest/meta-data/",
    "http://127.0.0.1:5432/",
    "http://10.0.0.5/admin",
    "http://192.168.1.1/",
    "https://localhost/internal",
    "http://[::1]/",
    "https://db.internal/query",
    "ftp://example.com/x",
    "http://user:pass@example.com/",
])
def test_ssrf_blocks_internal_and_bad(url):
    assert classify_fetch_target(url).blocked


def test_ssrf_allows_public():
    d = classify_fetch_target("https://api.github.com/repos")
    assert d.allowed and d.risk_level == RiskLevel.LOW.value


def test_redirect_reuses_ssrf():
    assert is_safe_redirect("http://169.254.169.254/").blocked
    assert is_safe_redirect("https://example.com/next").allowed


# Acceptance 3: paths outside allowed roots are blocked (traversal + symlink)
def test_path_traversal_blocked(tmp_path):
    root = tmp_path / "data"
    root.mkdir()
    assert resolve_within_root(root, "../../etc/passwd").blocked
    assert resolve_within_root(root, "sub/ok.txt").allowed


def test_symlink_escape_blocked(tmp_path):
    root = tmp_path / "data"
    root.mkdir()
    outside = tmp_path / "secret.txt"
    outside.write_text("x", encoding="utf-8")
    link = root / "escape"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks not supported here")
    assert resolve_within_root(root, "escape").blocked


# Acceptance 6: logs contain no controllable newlines or control characters
def test_log_forging_neutralized():
    safe, dec = sanitize_log_value("user\r\nADMIN authenticated=true")
    assert "\n" not in safe and "\r" not in safe
    assert dec.sanitized and dec.action != "allow"


def test_log_clean_value_untouched():
    safe, dec = sanitize_log_value("normal message")
    assert safe == "normal message" and dec.allowed


# oversized structured input
def test_oversized_csv_and_xml_blocked():
    assert tabular_within_limits("csv", size_bytes=200 * 1024 * 1024).blocked
    assert tabular_within_limits("xml", size_bytes=1, depth=500).blocked
    assert tabular_within_limits("json", size_bytes=10, depth=3).allowed


# Acceptance 5: approval replay is prevented (exactly-once)
def test_approval_replay_blocked():
    guard = ReplayGuard()
    assert guard.check("a-1", "hash").allowed
    assert guard.check("a-1", "hash").blocked          # same pair -> replay
    assert guard.check("a-1", "other-hash").allowed    # different payload -> fresh


# workspace crossing
def test_workspace_crossing_blocked():
    assert assert_same_workspace("ws-1", "ws-2").blocked
    assert assert_same_workspace("ws-1", "ws-1").allowed
    assert assert_same_workspace("", "").blocked       # empty actor ws is not a pass


# manifest signature (plugin / update)
def test_manifest_signature_enforced():
    keys = {"k1": b"trusted-key"}
    payload = b'{"version":"1.2.3"}'
    good = hmac.new(keys["k1"], payload, sha256).hexdigest()
    assert verify_manifest_signature(payload, signature_hex=good, signing_key_id="k1", trusted_keys=keys).allowed
    assert verify_manifest_signature(payload, signature_hex="", signing_key_id="", trusted_keys=keys).blocked
    assert verify_manifest_signature(payload, signature_hex=good, signing_key_id="unknown", trusted_keys=keys).blocked
    tampered = hmac.new(keys["k1"], b"other", sha256).hexdigest()
    assert verify_manifest_signature(payload, signature_hex=tampered, signing_key_id="k1", trusted_keys=keys).blocked


# Acceptance 2: manipulated identifiers / shell parameters are blocked
def test_sql_identifier_and_shell():
    assert safe_sql_identifier("user_events").allowed
    assert safe_sql_identifier("users; DROP TABLE x").blocked
    assert safe_sql_identifier("1_bad").blocked
    assert contains_shell_metacharacters("rm -rf / ; echo x")
    assert not contains_shell_metacharacters("plain_arg")


# decision record carries the full audit fields, no raw value leak
def test_decision_record_fields():
    d = classify_fetch_target("http://10.0.0.1/secret?token=sk-abc")
    data = d.to_dict()
    for key in ("rule_id", "risk_level", "reason", "source", "action", "blocked",
                "sanitized", "correlation_id", "audit_reference"):
        assert key in data
    # the inspected URL / token must never appear in the decision record
    blob = "|".join(str(v) for v in data.values())
    assert "sk-abc" not in blob and "10.0.0.1" not in blob


# Acceptance 8: all delta checks have a regression and the gate probe passes
def test_gate_delta_probe_all_pass():
    results = run_security_delta_checks()
    assert results and all(c["passed"] for c in results)
    assert {"ssrf", "path_escape", "log_forging", "approval_replay",
            "workspace_crossing", "manifest_signature"} <= {c["check_id"] for c in results}


def test_trust_and_risk_taxonomy():
    assert {t.value for t in TrustLevel} == {"trusted", "untrusted", "sanitized", "blocked"}
    assert {r.value for r in RiskLevel} == {"low", "medium", "high", "critical"}


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
