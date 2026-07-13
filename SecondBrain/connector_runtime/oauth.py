"""OAuth token access backed by the Secret Vault.

Tokens live ONLY in the vault. Callers pass a ``source_id``; the provider resolves
the access token at the moment of use and never returns it to logs or the cursor
store. A pluggable refresher can mint a new access token from the refresh token
and write it straight back into the vault.
"""

from __future__ import annotations

from typing import Callable

from secondbrain.connector_runtime.models import AuthError
from secondbrain.vault.store import SecretVault

WORKSPACE = "connectors"


class VaultTokenProvider:
    def __init__(self, vault: SecretVault, *, workspace: str = WORKSPACE) -> None:
        self.vault = vault
        self.workspace = workspace

    def _name(self, source_id: str, kind: str) -> str:
        return f"{source_id}.{kind}"

    def store_token(self, source_id: str, access_token: str, *, refresh_token: str | None = None) -> str:
        ref = self.vault.put_secret(self._name(source_id, "access_token"), access_token, workspace=self.workspace)
        if refresh_token:
            self.vault.put_secret(self._name(source_id, "refresh_token"), refresh_token, workspace=self.workspace)
        return ref

    def has_token(self, source_id: str) -> bool:
        return self.vault.exists(self._name(source_id, "access_token"), workspace=self.workspace)

    def get_access_token(self, source_id: str) -> str:
        if not self.has_token(source_id):
            raise AuthError(f"no access token for source {source_id!r}; authenticate first")
        return self.vault.get_secret(self._name(source_id, "access_token"), workspace=self.workspace)

    def refresh(self, source_id: str, refresher: Callable[[str], str]) -> str:
        """Mint a new access token from the stored refresh token and persist it."""
        refresh_name = self._name(source_id, "refresh_token")
        if not self.vault.exists(refresh_name, workspace=self.workspace):
            raise AuthError(f"no refresh token for source {source_id!r}")
        refresh_token = self.vault.get_secret(refresh_name, workspace=self.workspace)
        new_access = refresher(refresh_token)
        self.vault.put_secret(self._name(source_id, "access_token"), new_access, workspace=self.workspace)
        return new_access
