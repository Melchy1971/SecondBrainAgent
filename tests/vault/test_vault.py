"""Tests for the production secret vault (Task 2)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from secondbrain.vault import crypto
from secondbrain.vault.errors import DecryptionError, SecretNotFoundError
from secondbrain.vault.health import health_check
from secondbrain.vault.manager import SecretManager
from secondbrain.vault.migration import migrate_all
from secondbrain.vault.redaction import Redactor
from secondbrain.vault.references import is_reference, parse_reference
from secondbrain.vault.store import SecretVault

KEY_A = crypto.b64e(bytes(range(32)))
KEY_B = crypto.b64e(bytes(range(32, 64)))
SECRET = "sk-live-SUPERSECRET-abcdef1234567890"


def _env(key: str = KEY_A) -> dict:
    return {"SECONDBRAIN_VAULT_KEY": key}


def _vault(tmp_path: Path, key: str = KEY_A, **kw) -> SecretVault:
    return SecretVault(tmp_path / "vault", env=_env(key), redactor=Redactor(), **kw)


# --- encryption ----------------------------------------------------------------

def test_aesgcm_roundtrip_and_wrong_key():
    key = crypto.new_key()
    blob = crypto.encrypt(key, b"hello", aad=b"x")
    assert crypto.decrypt(key, blob, aad=b"x") == b"hello"
    with pytest.raises(DecryptionError):
        crypto.decrypt(crypto.new_key(), blob, aad=b"x")
    with pytest.raises(DecryptionError):
        crypto.decrypt(key, blob, aad=b"different-aad")


def test_secret_stored_encrypted_on_disk(tmp_path):
    vault = _vault(tmp_path)
    vault.put_secret("OPENAI_API_KEY", SECRET)
    raw = (tmp_path / "vault" / "vault.json").read_text(encoding="utf-8")
    assert SECRET not in raw  # never persisted in plaintext
    assert vault.get_secret("OPENAI_API_KEY") == SECRET


# --- references & workspace isolation -----------------------------------------

def test_put_returns_reference_not_value(tmp_path):
    vault = _vault(tmp_path)
    ref = vault.put_secret("token", SECRET, workspace="gmail")
    assert is_reference(ref)
    assert parse_reference(ref).workspace == "gmail"
    assert vault.resolve(ref) == SECRET


def test_workspace_isolation(tmp_path):
    vault = _vault(tmp_path)
    vault.put_secret("token", "value-a", workspace="gmail")
    vault.put_secret("token", "value-b", workspace="github")
    assert vault.get_secret("token", workspace="gmail") == "value-a"
    assert vault.get_secret("token", workspace="github") == "value-b"
    with pytest.raises(SecretNotFoundError):
        vault.get_secret("token", workspace="drive")


def test_list_secrets_has_no_values(tmp_path):
    vault = _vault(tmp_path)
    vault.put_secret("k", SECRET)
    rows = vault.list_secrets()
    blob = json.dumps(rows)
    assert SECRET not in blob
    assert rows[0]["reference"] == "secret://default/k"


# --- rotation ------------------------------------------------------------------

def test_key_rotation_reencrypts_and_preserves_values(tmp_path):
    vault = _vault(tmp_path)
    vault.put_secret("a", "alpha")
    vault.put_secret("b", "beta")
    ct_before = json.loads((tmp_path / "vault" / "vault.json").read_text())["secrets"]["default/a"]["ciphertext"]
    v1 = vault.active_dek_version
    v2 = vault.rotate_data_key()
    assert v2 == v1 + 1
    ct_after = json.loads((tmp_path / "vault" / "vault.json").read_text())["secrets"]["default/a"]["ciphertext"]
    assert ct_after != ct_before
    assert vault.get_secret("a") == "alpha"
    assert vault.get_secret("b") == "beta"
    assert any(e["action"] == "rotate_data_key" for e in vault.audit.entries())


def test_wrong_master_key_cannot_decrypt(tmp_path):
    vault = _vault(tmp_path, key=KEY_A)
    vault.put_secret("a", "alpha")
    reopened = _vault(tmp_path, key=KEY_B)
    assert reopened.canary_ok() is False
    with pytest.raises(DecryptionError):
        reopened.get_secret("a")


def test_reopen_with_same_key_reads_secrets(tmp_path):
    _vault(tmp_path, key=KEY_A).put_secret("a", "alpha")
    assert _vault(tmp_path, key=KEY_A).get_secret("a") == "alpha"


# --- redaction -----------------------------------------------------------------

def test_redactor_masks_registered_and_patterned_values():
    r = Redactor()
    r.register(SECRET)
    assert SECRET not in r.redact_text(f"log line key={SECRET} done")
    assert "***REDACTED***" in r.redact_text(f"log line key={SECRET} done")
    obj = {"api_key": "abc123def456", "note": f"used {SECRET}", "list": [SECRET]}
    red = r.redact_obj(obj)
    assert red["api_key"] == "***REDACTED***"
    assert SECRET not in json.dumps(red)


def test_get_registers_value_in_redactor(tmp_path):
    redactor = Redactor()
    vault = SecretVault(tmp_path / "vault", env=_env(), redactor=redactor)
    vault.put_secret("k", SECRET)
    assert SECRET not in redactor.redact_text(f"report: {SECRET}")


def test_audit_contains_no_secret_value(tmp_path):
    vault = _vault(tmp_path)
    vault.put_secret("k", SECRET)
    vault.get_secret("k")
    blob = json.dumps(vault.audit.entries())
    assert SECRET not in blob
    actions = {e["action"] for e in vault.audit.entries()}
    assert {"create", "read"} <= actions


# --- migration -----------------------------------------------------------------

def test_migration_moves_plaintext_into_vault(tmp_path):
    project = tmp_path / "proj"
    (project / "config").mkdir(parents=True)
    (project / "config" / "secrets.local.yaml").write_text(
        'openai:\n  api_key: "yaml-secret-value-123"\n', encoding="utf-8")
    (project / ".env").write_text(
        "OPENAI_API_KEY=env-secret-value-456\nAPP_NAME=keepme\n", encoding="utf-8")
    vault = _vault(tmp_path)
    report = migrate_all(vault, project, rewrite_env=True)
    assert report["count"] == 2
    assert vault.get_secret("openai.api_key") == "yaml-secret-value-123"
    assert vault.get_secret("OPENAI_API_KEY") == "env-secret-value-456"
    env_text = (project / ".env").read_text(encoding="utf-8")
    assert "env-secret-value-456" not in env_text
    assert "secret://default/OPENAI_API_KEY" in env_text
    assert "APP_NAME=keepme" in env_text
    assert list(project.glob(".env.bak-*"))


# --- health --------------------------------------------------------------------

def test_health_pass_and_leak_detection(tmp_path):
    vault = _vault(tmp_path)
    vault.put_secret("k", SECRET)
    ok = health_check(vault)
    assert ok["ok"] is True and ok["canary_ok"] is True
    leak_file = tmp_path / "logs.txt"
    leak_file.write_text(f"accidentally logged {SECRET}", encoding="utf-8")
    bad = health_check(vault, scan_paths=[leak_file])
    assert bad["ok"] is False
    assert bad["leaks"][0]["name"] == "k"
    assert "plaintext_secret_leak_detected" in bad["blockers"]


# --- import / export -----------------------------------------------------------

def test_encrypted_export_import_roundtrip(tmp_path):
    src = _vault(tmp_path)
    src.put_secret("a", "alpha", workspace="gmail")
    src.put_secret("b", "beta")
    bundle = tmp_path / "bundle.json"
    src.export_encrypted(bundle, "transfer-pass")
    raw = bundle.read_text(encoding="utf-8")
    assert "alpha" not in raw and "beta" not in raw
    dst = SecretVault(tmp_path / "vault2", env=_env(KEY_B), redactor=Redactor())
    count = dst.import_encrypted(bundle, "transfer-pass")
    assert count == 2
    assert dst.get_secret("a", workspace="gmail") == "alpha"
    with pytest.raises(DecryptionError):
        SecretVault(tmp_path / "vault3", env=_env(), redactor=Redactor()).import_encrypted(bundle, "wrong-pass")


# --- GUI controller ------------------------------------------------------------

def test_manager_rows_have_no_values_and_reveal_works(tmp_path):
    mgr = SecretManager(tmp_path / "vault", env=_env())
    mgr.add_secret("k", SECRET)
    rows = mgr.rows()
    assert rows[0]["value_masked"] == "********"
    assert SECRET not in json.dumps(rows)
    assert mgr.reveal_secret("k") == SECRET


def test_controller_run_async_delivers_result(tmp_path):
    from secondbrain.gui.secret_manager_panel import SecretManagerController
    mgr = SecretManager(tmp_path / "vault", env=_env())
    controller = SecretManagerController(mgr)
    delivered = {}
    thread = controller.run_async(controller.rotate, lambda r: delivered.update(v=r))
    thread.join(timeout=5)
    assert delivered["v"] >= 2
