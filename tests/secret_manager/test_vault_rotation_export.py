import pytest
from secondbrain.secret_manager.vault import (
    SecretVault, VaultLockedError, SecretNotFoundError, VaultError)


def _vault(tmp_path, pw="master"):
    return SecretVault.create(tmp_path / "v.json", pw)


def test_set_get_list_no_values(tmp_path):
    v = _vault(tmp_path)
    v.set_secret("API", "sk-123", secret_type="api_key")
    assert v.get_secret("API") == "sk-123"
    listing = v.list_secrets()
    assert listing[0]["name"] == "API" and listing[0]["type"] == "api_key"
    assert all("sk-123" not in str(item) for item in listing)   # never leaks value


def test_wrong_password_rejected(tmp_path):
    _vault(tmp_path, "right")
    v2 = SecretVault(tmp_path / "v.json")
    with pytest.raises(VaultLockedError):
        v2.unlock("wrong")


def test_locked_vault_blocks_access(tmp_path):
    v = _vault(tmp_path); v.set_secret("A", "x"); v.lock()
    with pytest.raises(VaultLockedError):
        v.get_secret("A")


def test_version_bump_and_unknown_type(tmp_path):
    v = _vault(tmp_path)
    v.set_secret("A", "1"); v.set_secret("A", "2")
    assert v.list_secrets()[0]["version"] == 2 and v.get_secret("A") == "2"
    with pytest.raises(VaultError):
        v.set_secret("B", "x", secret_type="nope")


def test_rotate_master_key_reencrypts(tmp_path):
    v = _vault(tmp_path)
    v.set_secret("A", "sk-secret", secret_type="api_key")
    ct_before = v._data["secrets"]["A"]["ct"]
    v.rotate_master_key("master")
    ct_after = v._data["secrets"]["A"]["ct"]
    assert ct_before != ct_after                       # ciphertext changed
    assert v.get_secret("A") == "sk-secret"            # plaintext preserved


def test_change_password(tmp_path):
    v = _vault(tmp_path); v.set_secret("A", "x")
    v.change_password("master", "new")
    fresh = SecretVault(tmp_path / "v.json")
    with pytest.raises(VaultLockedError):
        fresh.unlock("master")
    fresh.unlock("new")
    assert fresh.get_secret("A") == "x"


def test_export_import_roundtrip(tmp_path):
    v = _vault(tmp_path); v.set_secret("A", "val-A"); v.set_secret("B", "val-B")
    bundle = v.export_bundle("exp-pw")
    assert "val-A" not in str(bundle)                  # bundle is encrypted
    target = SecretVault.create(tmp_path / "t.json", "m2")
    assert target.import_bundle(bundle, "exp-pw")["imported"] == 2
    assert target.get_secret("A") == "val-A"
    with pytest.raises(VaultError):
        SecretVault.create(tmp_path / "t3.json", "m3").import_bundle(bundle, "wrong")
