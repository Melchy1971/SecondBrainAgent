"""Vault health check.

Verifies the vault can be opened and decrypted, and optionally scans given files
for plaintext leaks of stored secret values. The scan reports which file leaked
which secret *name* - never the secret value itself.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from secondbrain.vault.store import SecretVault


def scan_for_plaintext_leaks(vault: SecretVault, paths: list[str | Path]) -> list[dict[str, str]]:
    """Return a list of {file, workspace, name} where a secret value appears verbatim."""
    values: list[tuple[str, str, str]] = []
    for record in vault.list_secrets(include_system=False):
        value = vault.get_secret(record["name"], workspace=record["workspace"], audit=False)
        if value:
            values.append((record["workspace"], record["name"], value))

    leaks: list[dict[str, str]] = []
    for path in paths:
        p = Path(path)
        files = [p] if p.is_file() else (p.rglob("*") if p.is_dir() else [])
        for file in files:
            if not Path(file).is_file():
                continue
            try:
                text = Path(file).read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for workspace, name, value in values:
                if value in text:
                    leaks.append({"file": str(file), "workspace": workspace, "name": name})
    return leaks


def health_check(vault: SecretVault, *, scan_paths: list[str | Path] | None = None) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []

    canary = vault.canary_ok()
    if not canary:
        blockers.append("canary_decrypt_failed")

    leaks: list[dict[str, str]] = []
    if scan_paths:
        leaks = scan_for_plaintext_leaks(vault, scan_paths)
        if leaks:
            blockers.append("plaintext_secret_leak_detected")

    return {
        "schema": "secondbrain.vault.health.v1",
        "status": "pass" if not blockers else "blocked",
        "ok": not blockers,
        "canary_ok": canary,
        "secret_count": vault.secret_count(),
        "active_dek_version": vault.active_dek_version,
        "dek_versions": vault.dek_versions(),
        "leaks": leaks,
        "blockers": blockers,
        "warnings": warnings,
    }
