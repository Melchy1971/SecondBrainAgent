import json
from launcher import main
from secondbrain.release.connector_e2e_gate import (
    BLOCKED,
    CONDITIONAL_PASS,
    _configured,
    _evidence_complete,
    _safe_error,
    run_connector_e2e_gate,
)


def test_optional_unconfigured_connectors_are_conditional(tmp_path):
    report = run_connector_e2e_gate(tmp_path, env={})
    assert report["status"] == CONDITIONAL_PASS
    assert report["test_accounts_only"] and report["writes_require_approval"]


def test_required_unconfigured_connector_blocks(tmp_path):
    report = run_connector_e2e_gate(tmp_path, env={"REQUIRED_E2E_CONNECTORS": "google"})
    assert report["status"] == BLOCKED and report["failed_connectors"] == ["google"]


def test_test_account_marker_must_be_explicitly_enabled():
    env = {"GOOGLE_E2E_TEST_ACCOUNT": "0", "GOOGLE_CLIENT_ID": "id", "GOOGLE_CLIENT_SECRET": "secret",
           "GOOGLE_E2E_TOKEN_STORE": "token.json"}
    assert not _configured(env)[0]["configured"]


def test_unknown_required_connector_blocks(tmp_path):
    report = run_connector_e2e_gate(tmp_path, env={"REQUIRED_E2E_CONNECTORS": "google,typo"})
    assert report["status"] == BLOCKED
    assert report["failed_connectors"] == ["google", "typo"]


def test_required_connector_names_are_case_insensitive(tmp_path):
    report = run_connector_e2e_gate(tmp_path, env={"REQUIRED_E2E_CONNECTORS": " Google "})
    assert report["status"] == BLOCKED
    assert report["required_connectors"] == ["google"]


def test_cursor_evidence_is_required():
    staged = {"mail": True, "calendar": True}
    assert not _evidence_complete(True, True, False, staged)
    assert _evidence_complete(True, True, True, staged)


def test_configured_probe_stages_writes_without_secret_leak(tmp_path):
    def probe(config, _env, _root):
        return {"name": config["name"], "status": "approval_required", "account": "dedicated_test_account",
                "read_sync": True, "incremental_sync": True, "external_writes": 0}
    env = {"GOOGLE_E2E_TEST_ACCOUNT": "1", "GOOGLE_CLIENT_ID": "id", "GOOGLE_CLIENT_SECRET": "secret",
           "GOOGLE_E2E_TOKEN_STORE": "token.json"}
    report = run_connector_e2e_gate(tmp_path, env=env, probe=probe)
    assert report["status"] == CONDITIONAL_PASS
    assert "secret" not in json.dumps(report)


def test_invalid_probe_status_blocks_instead_of_passing(tmp_path):
    def probe(config, _env, _root):
        return {"name": config["name"], "status": "unexpected"}

    env = {"GOOGLE_E2E_TEST_ACCOUNT": "1", "GOOGLE_CLIENT_ID": "id", "GOOGLE_CLIENT_SECRET": "secret",
           "GOOGLE_E2E_TOKEN_STORE": "token.json"}
    report = run_connector_e2e_gate(tmp_path, env=env, probe=probe)
    assert report["status"] == BLOCKED
    assert report["failed_connectors"] == ["google"]
    assert report["connectors"][0]["error"]["type"] == "InvalidProbeResult"


def test_live_errors_are_redacted():
    assert _safe_error(RuntimeError("access_token=secret host=private"))["message"] == "connector live operation failed"


def test_launcher_is_safe_without_configuration(tmp_path, monkeypatch, capsys):
    for key in ("GOOGLE_E2E_TEST_ACCOUNT", "M365_E2E_TEST_ACCOUNT", "REQUIRED_E2E_CONNECTORS"):
        monkeypatch.delenv(key, raising=False)
    assert main(["connector-e2e-gate", "--project-root", str(tmp_path)]) == 0
    assert '"status": "CONDITIONAL_PASS"' in capsys.readouterr().out
