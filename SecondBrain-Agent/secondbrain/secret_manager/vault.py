"""Encrypted secret vault with envelope encryption + rotation + export/import.

Master password -> scrypt KEK -> wraps a random AES-256 DEK -> encrypts secrets.
list_secrets() and health() NEVER return secret values. The DEK is held in a
zeroizable buffer and wiped on lock().
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from secondbrain.secret_manager.crypto import (
    KdfParams, derive_key, random_key, encrypt, decrypt, CryptoError,
)
from secondbrain.secret_manager.zeroize import SecretBytes
from secondbrain.secret_manager.audit import AuditLog

SECRET_TYPES = {"api_key", "oauth_token", "workspace_secret"}
FILE_VERSION = 1


class VaultError(RuntimeError):
    pass


class VaultLockedError(VaultError):
    pass


class SecretNotFoundError(VaultError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class SecretVault:
    def __init__(self, path: str | Path, *, audit: AuditLog | None = None) -> None:
        self.path = Path(path)
        self.audit = audit or AuditLog()
        self._dek: SecretBytes | None = None
        self._data: dict[str, Any] = self._read() if self.path.exists() else {}

    # ---- persistence ------------------------------------------------------
    def _read(self) -> dict:
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _write(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(self._data, indent=2), encoding="utf-8")
        tmp.replace(self.path)

    # ---- lifecycle --------------------------------------------------------
    @classmethod
    def create(cls, path: str | Path, password: str, *, audit: AuditLog | None = None) -> "SecretVault":
        vault = cls(path, audit=audit)
        if vault.path.exists() and vault._data.get("wrapped_dek"):
            raise VaultError("vault already exists")
        params = KdfParams.new()
        kek = derive_key(password, params)
        dek = random_key()
        vault._data = {
            "version": FILE_VERSION,
            "kdf": params.to_dict(),
            "wrapped_dek": encrypt(kek, dek, aad=b"dek"),
            "secrets": {},
            "created_at": _now(),
        }
        vault._write()
        vault._dek = SecretBytes(dek)
        vault.audit.record("create")
        return vault

    def unlock(self, password: str) -> None:
        if not self._data.get("wrapped_dek"):
            raise VaultError("vault not initialized")
        params = KdfParams.from_dict(self._data["kdf"])
        kek = derive_key(password, params)
        try:
            dek = decrypt(kek, self._data["wrapped_dek"], aad=b"dek")
        except CryptoError as exc:
            self.audit.record("unlock", ok=False)
            raise VaultLockedError("invalid master password") from exc
        self._dek = SecretBytes(dek)
        self.audit.record("unlock")

    def lock(self) -> None:
        if self._dek is not None:
            self._dek.zeroize()
            self._dek = None
        self.audit.record("lock")

    @property
    def is_unlocked(self) -> bool:
        return self._dek is not None and not self._dek.cleared

    def _require(self) -> bytes:
        if not self.is_unlocked:
            raise VaultLockedError("vault is locked")
        return self._dek.bytes()

    # ---- secrets ----------------------------------------------------------
    def set_secret(self, name: str, value: str, *, secret_type: str = "workspace_secret") -> None:
        if secret_type not in SECRET_TYPES:
            raise VaultError(f"unknown secret type: {secret_type}")
        dek = self._require()
        existing = self._data.setdefault("secrets", {}).get(name)
        version = (existing["version"] + 1) if existing else 1
        blob = encrypt(dek, value.encode("utf-8"), aad=name.encode("utf-8"))
        self._data["secrets"][name] = {"type": secret_type, "version": version,
                                       "updated_at": _now(), **blob}
        self._write()
        self.audit.record("set", name=name, secret_type=secret_type, detail={"version": version})

    def get_secret(self, name: str) -> str:
        dek = self._require()
        entry = self._data.get("secrets", {}).get(name)
        if not entry:
            raise SecretNotFoundError(name)
        value = decrypt(dek, {"nonce": entry["nonce"], "ct": entry["ct"]}, aad=name.encode("utf-8"))
        self.audit.record("get", name=name, secret_type=entry.get("type"))
        return value.decode("utf-8")

    def delete(self, name: str) -> bool:
        existed = name in self._data.get("secrets", {})
        if existed:
            del self._data["secrets"][name]
            self._write()
            self.audit.record("delete", name=name)
        return existed

    def list_secrets(self) -> list[dict]:
        """Metadata only - never returns values."""
        return [{"name": n, "type": e["type"], "version": e["version"], "updated_at": e["updated_at"]}
                for n, e in sorted(self._data.get("secrets", {}).items())]

    # ---- rotation ---------------------------------------------------------
    def change_password(self, old_password: str, new_password: str) -> None:
        self.unlock(old_password)
        dek = self._require()
        params = KdfParams.new()
        new_kek = derive_key(new_password, params)
        self._data["kdf"] = params.to_dict()
        self._data["wrapped_dek"] = encrypt(new_kek, dek, aad=b"dek")
        self._write()
        self.audit.record("change_password")

    def rotate_master_key(self, password: str) -> dict:
        """Re-encrypt every secret under a fresh DEK (data-key rotation)."""
        self.unlock(password)
        old_dek = self._require()
        new_dek = random_key()
        rotated = 0
        for name, entry in self._data.get("secrets", {}).items():
            plaintext = decrypt(old_dek, {"nonce": entry["nonce"], "ct": entry["ct"]}, aad=name.encode("utf-8"))
            blob = encrypt(new_dek, plaintext, aad=name.encode("utf-8"))
            entry.update(blob)
            rotated += 1
        params = KdfParams.from_dict(self._data["kdf"])
        kek = derive_key(password, params)
        self._data["wrapped_dek"] = encrypt(kek, new_dek, aad=b"dek")
        self._write()
        self._dek = SecretBytes(new_dek)
        self.audit.record("rotate_master_key", detail={"rotated": rotated})
        return {"rotated": rotated}

    def rotate_secret(self, name: str, new_value: str) -> None:
        entry = self._data.get("secrets", {}).get(name)
        if not entry:
            raise SecretNotFoundError(name)
        self.set_secret(name, new_value, secret_type=entry["type"])
        self.audit.record("rotate_secret", name=name)

    # ---- portable export / import ----------------------------------------
    def export_bundle(self, export_password: str) -> dict:
        """Portable, self-contained encrypted bundle keyed by export_password."""
        dek = self._require()
        params = KdfParams.new()
        export_kek = derive_key(export_password, params)
        export_dek = random_key()
        secrets = {}
        for name, entry in self._data.get("secrets", {}).items():
            pt = decrypt(dek, {"nonce": entry["nonce"], "ct": entry["ct"]}, aad=name.encode("utf-8"))
            secrets[name] = {"type": entry["type"], **encrypt(export_dek, pt, aad=name.encode("utf-8"))}
        self.audit.record("export", detail={"count": len(secrets)})
        return {"version": FILE_VERSION, "kdf": params.to_dict(),
                "wrapped_dek": encrypt(export_kek, export_dek, aad=b"dek"), "secrets": secrets}

    def import_bundle(self, bundle: dict, export_password: str) -> dict:
        if not self.is_unlocked:
            raise VaultLockedError("unlock the vault before importing")
        params = KdfParams.from_dict(bundle["kdf"])
        export_kek = derive_key(export_password, params)
        try:
            export_dek = decrypt(export_kek, bundle["wrapped_dek"], aad=b"dek")
        except CryptoError as exc:
            raise VaultError("invalid export password") from exc
        imported = 0
        for name, entry in bundle.get("secrets", {}).items():
            pt = decrypt(export_dek, {"nonce": entry["nonce"], "ct": entry["ct"]}, aad=name.encode("utf-8"))
            self.set_secret(name, pt.decode("utf-8"), secret_type=entry.get("type", "workspace_secret"))
            imported += 1
        self.audit.record("import", detail={"count": imported})
        return {"imported": imported}
