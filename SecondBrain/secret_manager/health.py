"""Vault health (no secret values)."""

from __future__ import annotations

from collections import Counter
from typing import Any, Mapping

from secondbrain.secret_manager.vault import SecretVault


def key_backend_health(env: Mapping[str, str] | None = None) -> dict[str, Any]:
    """Redigierte Health des Master-Key-Backends (OS-Keyring/Env).

    Enthaelt nie Key, Klartext-Alias oder Pfad -- siehe key_provider.
    """
    from secondbrain.secret_manager.key_provider import key_provider_health
    return key_provider_health(env)


def vault_health(vault: SecretVault) -> dict:
    secrets = vault.list_secrets()
    by_type = Counter(s["type"] for s in secrets)
    kdf = vault._data.get("kdf", {})  # noqa: SLF001 - health inspection, no secret material
    return {
        "status": "PASS" if vault.path.exists() and vault._data.get("wrapped_dek") else "FAIL",
        "initialized": bool(vault._data.get("wrapped_dek")),
        "unlocked": vault.is_unlocked,
        "secret_count": len(secrets),
        "by_type": dict(by_type),
        "kdf": {"algo": kdf.get("algo"), "n": kdf.get("n"), "r": kdf.get("r"), "p": kdf.get("p")},
        "path": str(vault.path),
    }
