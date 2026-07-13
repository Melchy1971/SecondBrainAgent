"""AES-256-GCM primitives for the secret vault.

Every ciphertext is authenticated (GCM tag) and prefixed with a random 96-bit
nonce. Wrong key or tampering raises ``DecryptionError`` - decryption never
returns a fake/empty plaintext.
"""

from __future__ import annotations

import base64
import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

from secondbrain.vault.errors import DecryptionError

KEY_SIZE = 32          # AES-256
NONCE_SIZE = 12        # 96-bit GCM nonce
_SCRYPT_N = 2 ** 15
_SCRYPT_R = 8
_SCRYPT_P = 1


def new_key() -> bytes:
    """Return 32 cryptographically random bytes (AES-256 key)."""
    return os.urandom(KEY_SIZE)


def new_salt(size: int = 16) -> bytes:
    return os.urandom(size)


def derive_key_from_passphrase(passphrase: str, salt: bytes) -> bytes:
    """Derive a 32-byte key from a passphrase using scrypt."""
    kdf = Scrypt(salt=salt, length=KEY_SIZE, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P)
    return kdf.derive(passphrase.encode("utf-8"))


def b64e(raw: bytes) -> str:
    return base64.b64encode(raw).decode("ascii")


def b64d(text: str) -> bytes:
    return base64.b64decode(text.encode("ascii"))


def encrypt(key: bytes, plaintext: bytes, aad: bytes = b"") -> str:
    """Encrypt ``plaintext`` -> base64(nonce || ciphertext+tag)."""
    if len(key) != KEY_SIZE:
        raise ValueError("AES-256-GCM requires a 32-byte key")
    nonce = os.urandom(NONCE_SIZE)
    ct = AESGCM(key).encrypt(nonce, plaintext, aad)
    return b64e(nonce + ct)


def decrypt(key: bytes, blob_b64: str, aad: bytes = b"") -> bytes:
    """Decrypt base64(nonce || ciphertext) -> plaintext, or raise DecryptionError."""
    if len(key) != KEY_SIZE:
        raise ValueError("AES-256-GCM requires a 32-byte key")
    try:
        raw = b64d(blob_b64)
    except Exception as exc:  # noqa: BLE001 - malformed input boundary
        raise DecryptionError("ciphertext is not valid base64") from exc
    if len(raw) < NONCE_SIZE + 16:
        raise DecryptionError("ciphertext too short")
    nonce, ct = raw[:NONCE_SIZE], raw[NONCE_SIZE:]
    try:
        return AESGCM(key).decrypt(nonce, ct, aad)
    except InvalidTag as exc:
        raise DecryptionError("authentication failed: wrong key or tampered ciphertext") from exc


def wrap_key(kek: bytes, dek: bytes) -> str:
    """Wrap a data-encryption key with the key-encryption key."""
    return encrypt(kek, dek, aad=b"vault-dek-wrap")


def unwrap_key(kek: bytes, wrapped_b64: str) -> bytes:
    """Unwrap a data-encryption key, or raise DecryptionError."""
    return decrypt(kek, wrapped_b64, aad=b"vault-dek-wrap")
