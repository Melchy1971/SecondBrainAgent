"""Encrypted secret store (AES-256-GCM, envelope-encrypted).

Design:
- A master key (KEK) is resolved from env/passphrase/key file and never persisted
  inside the vault file.
- Data-encryption keys (DEKs) are generated per vault, wrapped by the KEK, and
  versioned. Secrets are encrypted with the active DEK.
- Key rotation generates a new DEK version and re-encrypts every secret, so a
  rotation invalidates all previous ciphertexts.
- Secrets are bound to ``workspace/name`` via AES-GCM additional authenticated
  data, giving workspace isolation and preventing ciphertext relocation.

Callers receive references (``secret://workspace/name``); plaintext is only
returned by an explicit ``get_secret``/``resolve`` at the point of use, and every
resolved value is registered with the redactor.
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from secondbrain.vault import crypto
from secondbrain.vault.audit import VaultAudit
from secondbrain.vault.errors import DecryptionError, SecretNotFoundError, VaultError
from secondbrain.vault.keys import MasterKeyProvider
from secondbrain.vault.redaction import Redactor, get_default_redactor
from secondbrain.vault.references import SecretRef, format_reference, parse_reference

SCHEMA = "secondbrain.vault.v1"
CANARY_NAME = "__canary__"
CANARY_WORKSPACE = "__vault__"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _entry_key(workspace: str, name: str) -> str:
    return f"{workspace}/{name}"


def _aad(workspace: str, name: str) -> bytes:
    return _entry_key(workspace, name).encode("utf-8")


class SecretVault:
    def __init__(
        self,
        vault_dir: str | Path,
        *,
        env: Mapping[str, str] | None = None,
        allow_generate: bool = True,
        audit: VaultAudit | None = None,
        redactor: Redactor | None = None,
        actor: str = "system",
    ) -> None:
        self.vault_dir = Path(vault_dir)
        self.vault_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.vault_dir / "vault.json"
        self.env = os.environ if env is None else env
        self.actor = actor
        self.audit = audit or VaultAudit(self.vault_dir / "audit.jsonl")
        self.redactor = redactor or get_default_redactor()
        self._key_provider = MasterKeyProvider(self.vault_dir, self.env, allow_generate=allow_generate)
        self._data: dict[str, Any] = self._load_or_init()
        self._kek: bytes = self._resolve_kek()
        self._ensure_active_dek()

    # --- persistence -----------------------------------------------------------

    def _load_or_init(self) -> dict[str, Any]:
        if self.path.exists():
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if data.get("schema") != SCHEMA:
                raise VaultError(f"unsupported vault schema: {data.get('schema')!r}")
            return data
        return {"schema": SCHEMA, "kdf_salt": None, "active_dek": 0, "deks": {}, "secrets": {}}

    def _save(self) -> None:
        payload = json.dumps(self._data, ensure_ascii=False, indent=2, sort_keys=True)
        fd, tmp = tempfile.mkstemp(dir=str(self.vault_dir), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(payload)
            os.replace(tmp, self.path)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    # --- key management --------------------------------------------------------

    def _resolve_kek(self) -> bytes:
        salt_b64 = self._data.get("kdf_salt")
        salt = crypto.b64d(salt_b64) if salt_b64 else None
        kek, _source, used_salt = self._key_provider.resolve(salt)
        if used_salt is not None and not salt_b64:
            self._data["kdf_salt"] = crypto.b64e(used_salt)
            self._save()
        return kek

    def _ensure_active_dek(self) -> None:
        if int(self._data.get("active_dek", 0)) >= 1 and self._data.get("deks"):
            return
        dek = crypto.new_key()
        version = 1
        self._data["deks"] = {str(version): {"wrapped": crypto.wrap_key(self._kek, dek), "created_at": _now(), "retired": False}}
        self._data["active_dek"] = version
        self._save()
        # write a canary so health checks can verify decryptability
        self._put_raw(CANARY_WORKSPACE, CANARY_NAME, b"vault-canary", meta={"system": True}, audit_action=None)

    def _dek(self, version: int) -> bytes:
        rec = self._data["deks"].get(str(version))
        if not rec:
            raise VaultError(f"unknown DEK version {version}")
        return crypto.unwrap_key(self._kek, rec["wrapped"])

    @property
    def active_dek_version(self) -> int:
        return int(self._data.get("active_dek", 0))

    # --- core secret operations ------------------------------------------------

    def _put_raw(self, workspace: str, name: str, value: bytes, *, meta=None, audit_action="create") -> None:
        version = self.active_dek_version
        dek = self._dek(version)
        key = _entry_key(workspace, name)
        existing = self._data["secrets"].get(key)
        record = {
            "workspace": workspace,
            "name": name,
            "ciphertext": crypto.encrypt(dek, value, aad=_aad(workspace, name)),
            "dek_version": version,
            "created_at": existing["created_at"] if existing else _now(),
            "updated_at": _now(),
            "rotated_at": existing.get("rotated_at") if existing else None,
            "meta": meta if meta is not None else (existing.get("meta") if existing else {}),
        }
        self._data["secrets"][key] = record
        self._save()
        if audit_action:
            self.audit.record(audit_action, workspace=workspace, name=name, key_version=version, actor=self.actor)

    def put_secret(self, name: str, value: str, *, workspace: str = "default", meta: dict | None = None) -> str:
        """Store/overwrite a secret and return its reference (never the value)."""
        if not isinstance(value, str) or value == "":
            raise VaultError("secret value must be a non-empty string")
        action = "update" if self.exists(name, workspace=workspace) else "create"
        self._put_raw(workspace, name, value.encode("utf-8"), meta=meta, audit_action=action)
        self.redactor.register(value)
        return format_reference(workspace, name)

    def get_secret(self, name: str, *, workspace: str = "default", audit: bool = True) -> str:
        key = _entry_key(workspace, name)
        record = self._data["secrets"].get(key)
        if not record:
            raise SecretNotFoundError(f"secret {name!r} not found in workspace {workspace!r}")
        dek = self._dek(int(record["dek_version"]))
        plaintext = crypto.decrypt(dek, record["ciphertext"], aad=_aad(workspace, name)).decode("utf-8")
        self.redactor.register(plaintext)
        if audit:
            self.audit.record("read", workspace=workspace, name=name, key_version=int(record["dek_version"]), actor=self.actor)
        return plaintext

    def resolve(self, reference: str | SecretRef) -> str:
        ref = reference if isinstance(reference, SecretRef) else parse_reference(reference)
        return self.get_secret(ref.name, workspace=ref.workspace)

    def get_ref(self, name: str, *, workspace: str = "default") -> str:
        if not self.exists(name, workspace=workspace):
            raise SecretNotFoundError(f"secret {name!r} not found in workspace {workspace!r}")
        return format_reference(workspace, name)

    def exists(self, name: str, *, workspace: str = "default") -> bool:
        return _entry_key(workspace, name) in self._data["secrets"]

    def delete_secret(self, name: str, *, workspace: str = "default") -> bool:
        key = _entry_key(workspace, name)
        if key not in self._data["secrets"]:
            return False
        version = int(self._data["secrets"][key]["dek_version"])
        del self._data["secrets"][key]
        self._save()
        self.audit.record("delete", workspace=workspace, name=name, key_version=version, actor=self.actor)
        return True

    def list_secrets(self, *, workspace: str | None = None, include_system: bool = False) -> list[dict[str, Any]]:
        """Return metadata only - never ciphertext or plaintext."""
        out: list[dict[str, Any]] = []
        for record in self._data["secrets"].values():
            if record["workspace"] == CANARY_WORKSPACE and not include_system:
                continue
            if workspace is not None and record["workspace"] != workspace:
                continue
            out.append({
                "workspace": record["workspace"],
                "name": record["name"],
                "reference": format_reference(record["workspace"], record["name"]),
                "dek_version": record["dek_version"],
                "created_at": record["created_at"],
                "updated_at": record["updated_at"],
                "rotated_at": record.get("rotated_at"),
                "meta": record.get("meta", {}),
            })
        return sorted(out, key=lambda r: (r["workspace"], r["name"]))

    def workspaces(self) -> list[str]:
        return sorted({r["workspace"] for r in self._data["secrets"].values() if r["workspace"] != CANARY_WORKSPACE})

    # --- rotation --------------------------------------------------------------

    def rotate_data_key(self) -> int:
        """Generate a new DEK version and re-encrypt every secret under it."""
        new_version = max((int(v) for v in self._data["deks"]), default=0) + 1
        new_dek = crypto.new_key()
        old_deks = {int(v): self._dek(int(v)) for v in self._data["deks"]}
        for key, record in self._data["secrets"].items():
            old_dek = old_deks[int(record["dek_version"])]
            aad = _aad(record["workspace"], record["name"])
            plaintext = crypto.decrypt(old_dek, record["ciphertext"], aad=aad)
            record["ciphertext"] = crypto.encrypt(new_dek, plaintext, aad=aad)
            record["dek_version"] = new_version
            record["rotated_at"] = _now()
        for rec in self._data["deks"].values():
            rec["retired"] = True
        self._data["deks"][str(new_version)] = {"wrapped": crypto.wrap_key(self._kek, new_dek), "created_at": _now(), "retired": False}
        self._data["active_dek"] = new_version
        self._save()
        self.audit.record("rotate_data_key", key_version=new_version, actor=self.actor,
                          detail={"secrets": len(self._data["secrets"])})
        return new_version

    def rewrap_master_key(self, new_env: Mapping[str, str]) -> str:
        """Re-wrap all DEKs under a new master key (KEK rotation). Secrets untouched."""
        deks = {v: self._dek(int(v)) for v in self._data["deks"]}
        new_provider = MasterKeyProvider(self.vault_dir, new_env, allow_generate=False)
        new_kek, source, used_salt = new_provider.resolve(None)
        for v, dek in deks.items():
            self._data["deks"][v]["wrapped"] = crypto.wrap_key(new_kek, dek)
        if used_salt is not None:
            self._data["kdf_salt"] = crypto.b64e(used_salt)
        self._kek = new_kek
        self._key_provider = new_provider
        self.env = new_env
        self._save()
        self.audit.record("rewrap_master_key", actor=self.actor, detail={"source": source})
        return source

    # --- encrypted import / export --------------------------------------------

    def export_encrypted(self, path: str | Path, passphrase: str, *, workspace: str | None = None) -> Path:
        """Export secrets as a portable bundle encrypted with a passphrase."""
        items = []
        for record in self._data["secrets"].values():
            if record["workspace"] == CANARY_WORKSPACE:
                continue
            if workspace is not None and record["workspace"] != workspace:
                continue
            value = self.get_secret(record["name"], workspace=record["workspace"], audit=False)
            items.append({"workspace": record["workspace"], "name": record["name"], "value": value, "meta": record.get("meta", {})})
        salt = crypto.new_salt()
        key = crypto.derive_key_from_passphrase(passphrase, salt)
        blob = crypto.encrypt(key, json.dumps(items).encode("utf-8"), aad=b"vault-export")
        bundle = {"schema": "secondbrain.vault.export.v1", "kdf_salt": crypto.b64e(salt), "payload": blob}
        out = Path(path)
        out.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
        self.audit.record("export", actor=self.actor, detail={"count": len(items)})
        return out

    def import_encrypted(self, path: str | Path, passphrase: str, *, overwrite: bool = False) -> int:
        bundle = json.loads(Path(path).read_text(encoding="utf-8"))
        if bundle.get("schema") != "secondbrain.vault.export.v1":
            raise VaultError("unsupported export bundle schema")
        salt = crypto.b64d(bundle["kdf_salt"])
        key = crypto.derive_key_from_passphrase(passphrase, salt)
        try:
            items = json.loads(crypto.decrypt(key, bundle["payload"], aad=b"vault-export").decode("utf-8"))
        except DecryptionError:
            raise
        imported = 0
        for item in items:
            if not overwrite and self.exists(item["name"], workspace=item["workspace"]):
                continue
            self.put_secret(item["name"], item["value"], workspace=item["workspace"], meta=item.get("meta", {}))
            imported += 1
        self.audit.record("import", actor=self.actor, detail={"count": imported})
        return imported

    # --- health helpers --------------------------------------------------------

    def canary_ok(self) -> bool:
        try:
            return self.get_secret(CANARY_NAME, workspace=CANARY_WORKSPACE, audit=False) == "vault-canary"
        except (SecretNotFoundError, DecryptionError):
            return False

    def secret_count(self) -> int:
        return sum(1 for r in self._data["secrets"].values() if r["workspace"] != CANARY_WORKSPACE)

    def dek_versions(self) -> list[int]:
        return sorted(int(v) for v in self._data["deks"])
