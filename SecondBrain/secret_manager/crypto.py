"""AES-256-GCM envelope crypto (v30.66).

- Key derivation: scrypt (stdlib hashlib) from the master password -> 256-bit KEK.
- Data encryption key (DEK): random 256-bit AES key, wrapped by the KEK.
- Secrets are AES-256-GCM encrypted with the DEK (AAD-bound to the secret name).

Requires the `cryptography` package (see requirements-security.txt). No fake ciphers.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
from dataclasses import dataclass

KEY_LEN = 32          # AES-256
NONCE_LEN = 12        # GCM nonce
SCRYPT_N = 2 ** 14
SCRYPT_R = 8
SCRYPT_P = 1
SCRYPT_MAXMEM = 64 * 1024 * 1024


class CryptoError(RuntimeError):
    pass


def _aesgcm():
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        return AESGCM
    except Exception as exc:  # pragma: no cover - dependency guard
        raise CryptoError("cryptography package required (pip install -r requirements-security.txt)") from exc


def b64e(raw: bytes) -> str:
    return base64.b64encode(raw).decode("ascii")


def b64d(text: str) -> bytes:
    return base64.b64decode(text.encode("ascii"))


@dataclass(frozen=True)
class KdfParams:
    salt: str
    n: int = SCRYPT_N
    r: int = SCRYPT_R
    p: int = SCRYPT_P
    dklen: int = KEY_LEN

    def to_dict(self) -> dict:
        return {"algo": "scrypt", "salt": self.salt, "n": self.n, "r": self.r, "p": self.p, "dklen": self.dklen}

    @classmethod
    def new(cls) -> "KdfParams":
        return cls(salt=b64e(os.urandom(16)))

    @classmethod
    def from_dict(cls, d: dict) -> "KdfParams":
        return cls(salt=d["salt"], n=int(d["n"]), r=int(d["r"]), p=int(d["p"]), dklen=int(d.get("dklen", KEY_LEN)))


def derive_key(password: str, params: KdfParams) -> bytes:
    return hashlib.scrypt(password.encode("utf-8"), salt=b64d(params.salt),
                          n=params.n, r=params.r, p=params.p, dklen=params.dklen, maxmem=SCRYPT_MAXMEM)


def random_key() -> bytes:
    return os.urandom(KEY_LEN)


def encrypt(key: bytes, plaintext: bytes, *, aad: bytes = b"") -> dict:
    if len(key) != KEY_LEN:
        raise CryptoError("key must be 256-bit")
    nonce = os.urandom(NONCE_LEN)
    ct = _aesgcm()(key).encrypt(nonce, plaintext, aad)
    return {"nonce": b64e(nonce), "ct": b64e(ct)}


def decrypt(key: bytes, blob: dict, *, aad: bytes = b"") -> bytes:
    try:
        return _aesgcm()(key).decrypt(b64d(blob["nonce"]), b64d(blob["ct"]), aad)
    except CryptoError:
        raise
    except Exception as exc:  # cryptography.InvalidTag etc.
        raise CryptoError("decryption failed (wrong key or tampered data)") from exc


def constant_time_equal(a: bytes, b: bytes) -> bool:
    return hmac.compare_digest(a, b)
