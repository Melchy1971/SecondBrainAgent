"""Vault health (no secret values)."""

from __future__ import annotations

from collections import Counter
from secondbrain.secret_manager.vault import SecretVault


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
