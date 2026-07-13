"""Redaction-Middleware: maskiert Secrets in Strings und beliebig verschachtelten Payloads.

Baut auf secondbrain.safe_logging.redact (Pattern- und Vault-Redaction) auf und
ergänzt schlüsselbasierte Maskierung für bekannte Secret-Feldnamen.
"""

from __future__ import annotations

from typing import Any

from secondbrain.safe_logging import redact

MASK = "***REDACTED***"

SECRET_KEY_MARKERS = (
    "password", "passwort", "secret", "token", "api_key", "apikey",
    "authorization", "auth_header", "database_url", "dsn", "private_key",
    "client_secret", "access_key", "refresh_token", "credential",
)


def is_secret_key(key: str) -> bool:
    lowered = key.lower()
    return any(marker in lowered for marker in SECRET_KEY_MARKERS)


class RedactionMiddleware:
    """Wendet Redaction auf Log-/Audit-Payloads an, bevor sie persistiert werden."""

    def redact_text(self, text: str) -> str:
        return redact(text)

    def redact_payload(self, payload: Any, _depth: int = 0) -> Any:
        if _depth > 12:
            return MASK
        if isinstance(payload, dict):
            return {
                key: (MASK if is_secret_key(str(key)) and value not in (None, "", False)
                      else self.redact_payload(value, _depth + 1))
                for key, value in payload.items()
            }
        if isinstance(payload, (list, tuple)):
            return [self.redact_payload(item, _depth + 1) for item in payload]
        if isinstance(payload, str):
            return redact(payload)
        return payload
