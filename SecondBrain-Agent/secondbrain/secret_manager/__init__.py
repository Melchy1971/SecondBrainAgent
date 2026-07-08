"""AES-256 secret management (v30.66). No secrets in logs; real crypto only."""
from secondbrain.secret_manager.crypto import CryptoError
from secondbrain.secret_manager.vault import (
    SecretVault, VaultError, VaultLockedError, SecretNotFoundError, SECRET_TYPES,
)
from secondbrain.secret_manager.audit import AuditLog
from secondbrain.secret_manager.zeroize import SecretBytes, zeroize, zeroizing
from secondbrain.secret_manager.redaction import redact_text, redact_mapping, SecretRedactingFilter
from secondbrain.secret_manager.health import vault_health

__all__ = [
    "SecretVault", "VaultError", "VaultLockedError", "SecretNotFoundError", "SECRET_TYPES",
    "CryptoError", "AuditLog", "SecretBytes", "zeroize", "zeroizing",
    "redact_text", "redact_mapping", "SecretRedactingFilter", "vault_health",
]
