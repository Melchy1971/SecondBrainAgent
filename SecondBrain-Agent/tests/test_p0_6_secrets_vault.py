import json

import pytest

from secondbrain.production_core import ProductionCore


def test_secrets_are_encrypted_not_base64_encoded_plaintext(tmp_path):
    prod = ProductionCore(tmp_path)
    prod.vault.put("api_key", "secret-value")

    raw = json.loads((tmp_path / "data" / "production_core" / "secrets.json").read_text(encoding="utf-8"))
    record = raw[0]

    assert "value_enc" not in record
    assert "value_envelope" in record
    assert record["value_envelope"]["alg"] == "sb-local-v1"
    assert "secret-value" not in json.dumps(record)
    assert prod.vault.get("api_key") == "secret-value"


def test_secret_integrity_check_blocks_tampered_ciphertext(tmp_path):
    prod = ProductionCore(tmp_path)
    prod.vault.put("api_key", "secret-value")

    path = tmp_path / "data" / "production_core" / "secrets.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw[0]["value_envelope"]["ciphertext_b64"] = "AAAA"
    path.write_text(json.dumps(raw), encoding="utf-8")

    with pytest.raises(ValueError, match="secret_integrity_check_failed"):
        prod.vault.get("api_key")
