import pytest
from secondbrain.secret_manager.crypto import (
    KdfParams, derive_key, random_key, encrypt, decrypt, CryptoError, KEY_LEN)
from secondbrain.secret_manager.zeroize import SecretBytes, zeroize, zeroizing


def test_kdf_deterministic_same_params():
    p = KdfParams.new()
    assert derive_key("pw", p) == derive_key("pw", p)
    assert derive_key("pw", p) != derive_key("other", p)
    assert len(derive_key("pw", p)) == KEY_LEN


def test_aes_roundtrip_and_aad_binding():
    k = random_key()
    blob = encrypt(k, b"secret", aad=b"name1")
    assert decrypt(k, blob, aad=b"name1") == b"secret"
    with pytest.raises(CryptoError):
        decrypt(k, blob, aad=b"name2")            # AAD mismatch -> fails
    with pytest.raises(CryptoError):
        decrypt(random_key(), blob, aad=b"name1")  # wrong key -> fails


def test_secretbytes_zeroization():
    sb = SecretBytes(b"key-material")
    assert sb.bytes() == b"key-material"
    sb.zeroize()
    assert sb.cleared and "****" not in repr(sb) or "cleared" in repr(sb)
    with pytest.raises(ValueError):
        sb.bytes()


def test_zeroize_buffer_and_context():
    buf = bytearray(b"abc"); zeroize(buf); assert bytes(buf) == bytes(3)
    with zeroizing(b"xy") as b:
        assert bytes(b) == b"xy"
    assert bytes(b) == bytes(2)
