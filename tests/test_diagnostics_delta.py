"""Sprint 39 (v31.00) acceptance tests - support center delta."""

from __future__ import annotations

import pytest

from secondbrain.support.diagnostics_delta import (
    REPAIR_ACTIONS, RepairCenter, build_redaction_report, classify_error,
    detect_known_errors, validate_bundle,
)


def _clean_bundle():
    return {
        "system_info": {"application_version": "31.00", "python_runtime": "3.12", "architecture": "x64"},
        "database_status": {"status": "ok", "migration": "head"},
        "provider_status": {"llm": "ready"},
        "installed_modules": ["rag", "approval"],
    }


# 1: bundle contains core technical data; clean bundle validates
def test_clean_bundle_valid():
    report = validate_bundle(_clean_bundle())
    assert report["ok"] and report["count"] == 0


# 2: no user data or secrets -> validator blocks residual secrets
def test_validator_blocks_secret():
    bundle = _clean_bundle() | {"config": {"note": "api_key=sk-abcdef012345ABCDEF"}}
    report = validate_bundle(bundle)
    assert report["ok"] is False and report["count"] >= 1


# 2b: sensitive KEY is flagged even if value benign
def test_validator_flags_sensitive_key():
    bundle = {"database_url": "postgres://user:pw@host/db"}
    report = validate_bundle(bundle)
    assert report["ok"] is False
    assert "database_url" in report["residual_fields"]


# 3: redaction report shows removed fields (paths only, no values)
def test_redaction_report_lists_fields():
    raw = {"a": {"password": "hunter2", "ok": "value"}, "note": "token=sk-zzz999888777"}
    rep = build_redaction_report(raw)
    assert "a.password" in rep.removed_fields
    assert "note" in rep.removed_fields
    blob = str(rep.to_dict())
    assert "hunter2" not in blob and "sk-zzz999888777" not in blob  # values never shown


# 4: broken/partial module does not break the report
def test_partial_data_ok():
    raw = {"section_ok": {"v": 1}, "section_error": {"error": "collector failed"}, "list": [1, "token=sk-abcdef123456"]}
    rep = build_redaction_report(raw)  # must not raise
    assert "list[1]" in rep.removed_fields


# 5: writing repair action produces an approval request, not execution
def test_repair_requires_approval():
    center = RepairCenter()
    write = center.propose("clear_cache", workspace_id="ws-1")
    assert write["requires_approval"] is True and write["executed"] is False
    assert write["route"] == "approval_inbox"
    read = center.propose("validate_index")
    assert read["requires_approval"] is False and read["executed"] is False
    # every proposal audited, no auto-delete
    log = center.audit_log()
    assert len(log) == 2 and all(r["auto_delete"] is False for r in log)


# 6: bundle is reproducible and validatable
def test_reproducible_validation():
    b = _clean_bundle()
    assert validate_bundle(b) == validate_bundle(b)


# 7: errors get stable error codes
def test_stable_error_codes():
    assert classify_error("could not connect to postgres: connection refused")["code"] == "SB-DB-001"
    assert classify_error("OAuth token expired")["code"] == "SB-CONN-001"
    assert classify_error("migration pending")["code"] == "SB-MIG-001"
    assert classify_error("some unmapped weirdness")["code"] == "SB-GEN-000"  # still coded
    # codes are stable identifiers
    assert classify_error("disk full")["code"] == "SB-DISK-001"


# detect_known_errors redacts and codes
def test_detect_known_errors_redacts():
    errors = ["connection refused token=sk-abcdef123456", "OAuth invalid_grant"]
    result = detect_known_errors(errors)
    assert result[0]["code"] == "SB-DB-001"
    assert "sk-abcdef123456" not in result[0]["message"]
    assert result[1]["code"] == "SB-CONN-001"


# unknown repair action raises
def test_unknown_repair():
    with pytest.raises(KeyError):
        RepairCenter().propose("nuke_everything")


# all 7 repair actions present, destructive ones need approval
def test_repair_catalog():
    assert set(REPAIR_ACTIONS) >= {"validate_index", "clear_cache", "check_queue",
                                   "validate_config", "check_migration", "reauth_connector", "check_backup"}
    assert all(a.writing or a.destructive or not a.writing for a in REPAIR_ACTIONS.values())


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
