from secondbrain.secret_manager.vault import SecretVault
from secondbrain.secret_manager.health import vault_health


def test_health_reports_no_values(tmp_path):
    v = SecretVault.create(tmp_path / "v.json", "pw")
    v.set_secret("A", "secretval", secret_type="api_key")
    h = vault_health(v)
    assert h["status"] == "PASS" and h["initialized"] is True and h["unlocked"] is True
    assert h["secret_count"] == 1 and h["by_type"]["api_key"] == 1
    assert "secretval" not in str(h)
    assert h["kdf"]["algo"] == "scrypt"
