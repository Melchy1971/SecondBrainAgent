"""Production secret vault: AES-256-GCM encrypted secrets with references,
rotation, redaction, migration, health checks, and an audit trail.

Nothing here writes secret values to logs, reports, prompt history, or the audit
trail. Callers hold ``secret://`` references and resolve plaintext only at the
point of use.
"""

from secondbrain.vault.audit import VaultAudit
from secondbrain.vault.errors import (
    DecryptionError,
    MasterKeyError,
    SecretNotFoundError,
    SecretReferenceError,
    VaultError,
    VaultLockedError,
)
from secondbrain.vault.health import health_check, scan_for_plaintext_leaks
from secondbrain.vault.keys import MasterKeyProvider
from secondbrain.vault.manager import SecretManager
from secondbrain.vault.migration import migrate_all, migrate_env_secrets, migrate_yaml_secrets
from secondbrain.vault.redaction import Redactor, get_default_redactor, redact_obj, redact_text
from secondbrain.vault.references import SecretRef, format_reference, is_reference, parse_reference
from secondbrain.vault.store import SecretVault

__all__ = [
    "DecryptionError",
    "MasterKeyError",
    "MasterKeyProvider",
    "Redactor",
    "SecretManager",
    "SecretNotFoundError",
    "SecretRef",
    "SecretReferenceError",
    "SecretVault",
    "VaultAudit",
    "VaultError",
    "VaultLockedError",
    "format_reference",
    "get_default_redactor",
    "health_check",
    "is_reference",
    "migrate_all",
    "migrate_env_secrets",
    "migrate_yaml_secrets",
    "parse_reference",
    "redact_obj",
    "redact_text",
    "scan_for_plaintext_leaks",
]
