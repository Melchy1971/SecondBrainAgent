from __future__ import annotations

import base64
import hashlib
import hmac
import os
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


_KEY_STORE = "secrets_vault_key"
_SECRET_STORE = "secrets"
_NONCE_SIZE = 16
_KEY_SIZE = 32


class SecretsVault:
    """
    Local encrypted secret store for the production core scaffold.

    Design constraints:
    - Uses only Python stdlib to keep the project installable with the current minimal requirements.
    - Stores a per-environment master key outside the secret records.
    - Encrypts values with a derived SHA-256 keystream and authenticates ciphertext with HMAC-SHA256.

    This is a local-at-rest protection layer, not a replacement for OS keyring, DPAPI, Vault,
    SOPS, or cloud KMS in hardened deployments.
    """

    def __init__(self, store):
        self.store = store

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _master_key(self) -> bytes:
        configured = os.environ.get("SECONDBRAIN_SECRETS_KEY")
        if configured:
            return hashlib.sha256(configured.encode("utf-8")).digest()

        record = self.store.load(_KEY_STORE, {})
        encoded = record.get("key_b64")
        if encoded:
            return base64.b64decode(encoded.encode("ascii"))

        key = os.urandom(_KEY_SIZE)
        self.store.save(_KEY_STORE, {"key_b64": base64.b64encode(key).decode("ascii"), "created_at": self._now()})
        return key

    @staticmethod
    def _xor_stream(data: bytes, key: bytes, nonce: bytes) -> bytes:
        output = bytearray()
        counter = 0
        while len(output) < len(data):
            block = hashlib.sha256(key + nonce + counter.to_bytes(8, "big")).digest()
            output.extend(block)
            counter += 1
        return bytes(byte ^ stream for byte, stream in zip(data, output))

    def _encrypt(self, value: str) -> dict[str, str]:
        key = self._master_key()
        nonce = os.urandom(_NONCE_SIZE)
        plaintext = value.encode("utf-8")
        ciphertext = self._xor_stream(plaintext, key, nonce)
        mac = hmac.new(key, nonce + ciphertext, hashlib.sha256).hexdigest()
        return {
            "alg": "sb-local-v1",
            "nonce_b64": base64.b64encode(nonce).decode("ascii"),
            "ciphertext_b64": base64.b64encode(ciphertext).decode("ascii"),
            "mac": mac,
        }

    def _decrypt(self, envelope: dict[str, str]) -> str:
        if envelope.get("alg") != "sb-local-v1":
            raise ValueError("unsupported_secret_envelope")
        key = self._master_key()
        nonce = base64.b64decode(envelope["nonce_b64"].encode("ascii"))
        ciphertext = base64.b64decode(envelope["ciphertext_b64"].encode("ascii"))
        expected = hmac.new(key, nonce + ciphertext, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, envelope.get("mac", "")):
            raise ValueError("secret_integrity_check_failed")
        return self._xor_stream(ciphertext, key, nonce).decode("utf-8")

    def put(self, name: str, value: str, scope: str = "default") -> dict[str, Any]:
        if not name or not name.strip():
            raise ValueError("secret_name_required")
        secrets = self.store.load(_SECRET_STORE, [])
        item = {
            "id": str(uuid4()),
            "name": name.strip(),
            "scope": scope.strip() or "default",
            "value_envelope": self._encrypt(value),
            "created_at": self._now(),
            "status": "active",
        }
        secrets = [s for s in secrets if not (s.get("name") == item["name"] and s.get("scope") == item["scope"])]
        secrets.append(item)
        self.store.save(_SECRET_STORE, secrets)
        return {"id": item["id"], "name": item["name"], "scope": item["scope"], "status": "stored"}

    def get(self, name: str, scope: str = "default") -> str | None:
        for item in self.store.load(_SECRET_STORE, []):
            if item.get("name") == name and item.get("scope") == scope and item.get("status") == "active":
                envelope = item.get("value_envelope")
                if not isinstance(envelope, dict):
                    raise ValueError("invalid_secret_record")
                return self._decrypt(envelope)
        return None

    def list(self) -> list[dict[str, Any]]:
        redacted = []
        for item in self.store.load(_SECRET_STORE, []):
            redacted.append({k: v for k, v in item.items() if k not in {"value_enc", "value_envelope"}})
        return redacted

    def rotate(self, name: str, new_value: str, scope: str = "default") -> dict[str, Any]:
        existing = self.store.load(_SECRET_STORE, [])
        rotated_at = self._now()
        for item in existing:
            if item.get("name") == name and item.get("scope") == scope and item.get("status") == "active":
                item["status"] = "rotated"
                item["rotated_at"] = rotated_at
        self.store.save(_SECRET_STORE, existing)
        return self.put(name, new_value, scope)
