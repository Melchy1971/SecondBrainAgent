"""Master-key (KEK) resolution and handling.

Precedence: explicit env key > passphrase > key file. The master key is never
written to logs, reports, or the vault file. In production, provide the key via
``SECONDBRAIN_VAULT_KEY`` (base64 32 bytes) or ``SECONDBRAIN_VAULT_PASSPHRASE``;
the auto-generated key file is a development convenience only.
"""

from __future__ import annotations

import os
import stat
from pathlib import Path
from typing import Mapping

from secondbrain.vault.crypto import KEY_SIZE, b64d, b64e, derive_key_from_passphrase, new_key, new_salt
from secondbrain.vault.errors import MasterKeyError, VaultLockedError

ENV_KEY = "SECONDBRAIN_VAULT_KEY"
ENV_PASSPHRASE = "SECONDBRAIN_VAULT_PASSPHRASE"
KEYFILE_NAME = "master.key"


class MasterKeyProvider:
    """Resolves the key-encryption key (KEK) from the environment or a key file."""

    def __init__(
        self,
        vault_dir: str | Path,
        env: Mapping[str, str] | None = None,
        *,
        allow_generate: bool = True,
    ) -> None:
        self.vault_dir = Path(vault_dir)
        self.env = os.environ if env is None else env
        self.allow_generate = allow_generate

    @property
    def keyfile(self) -> Path:
        return self.vault_dir / KEYFILE_NAME

    def resolve(self, salt: bytes | None = None) -> tuple[bytes, str, bytes | None]:
        """Return ``(kek, source, salt)``. ``salt`` is non-None only for passphrase mode."""
        raw_env = str(self.env.get(ENV_KEY, "")).strip()
        if raw_env:
            try:
                kek = b64d(raw_env)
            except Exception as exc:  # noqa: BLE001
                raise MasterKeyError(f"{ENV_KEY} is not valid base64") from exc
            if len(kek) != KEY_SIZE:
                raise MasterKeyError(f"{ENV_KEY} must decode to {KEY_SIZE} bytes")
            return kek, "env", None

        passphrase = str(self.env.get(ENV_PASSPHRASE, "")).strip()
        if passphrase:
            used_salt = salt or new_salt()
            return derive_key_from_passphrase(passphrase, used_salt), "passphrase", used_salt

        if self.keyfile.exists():
            kek = b64d(self.keyfile.read_text(encoding="ascii").strip())
            if len(kek) != KEY_SIZE:
                raise MasterKeyError("master key file is corrupt (wrong length)")
            return kek, "keyfile", None

        if not self.allow_generate:
            raise VaultLockedError(
                "no master key available: set SECONDBRAIN_VAULT_KEY or "
                "SECONDBRAIN_VAULT_PASSPHRASE, or provide a master key file"
            )
        return self._generate_keyfile(), "keyfile-generated", None

    def _generate_keyfile(self) -> bytes:
        self.vault_dir.mkdir(parents=True, exist_ok=True)
        kek = new_key()
        self.keyfile.write_text(b64e(kek), encoding="ascii")
        try:
            os.chmod(self.keyfile, stat.S_IRUSR | stat.S_IWUSR)
        except OSError:
            pass
        return kek

    @staticmethod
    def generate_env_key() -> str:
        """Return a fresh base64 master key suitable for SECONDBRAIN_VAULT_KEY."""
        return b64e(new_key())
