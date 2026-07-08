"""Vault error hierarchy. Error messages never contain secret values."""

from __future__ import annotations


class VaultError(RuntimeError):
    """Base error for all vault operations."""


class VaultLockedError(VaultError):
    """Raised when the master key is unavailable and the vault cannot be opened."""


class MasterKeyError(VaultError):
    """Raised when the master key material is missing or malformed."""


class DecryptionError(VaultError):
    """Raised when ciphertext cannot be authenticated/decrypted (wrong key or tampering)."""


class SecretNotFoundError(VaultError):
    """Raised when a referenced secret does not exist in the requested workspace."""


class SecretReferenceError(VaultError):
    """Raised when a secret reference string is malformed."""
