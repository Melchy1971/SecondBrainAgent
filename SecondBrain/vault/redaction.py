"""Redaction engine for logs, reports, prompt history, and the audit trail.

Two layers:
1. Known-value redaction - exact secret values registered by the vault when a
   secret is created or resolved are masked wherever they appear.
2. Pattern/key redaction - fallback for values that were never registered
   (api-key/token/password patterns, and sensitive JSON keys).

The goal: even if a caller accidentally puts a resolved secret into a log line or
a JSON report, ``redact_text`` / ``redact_obj`` remove it before it is persisted.
"""

from __future__ import annotations

import re
from typing import Any

PLACEHOLDER = "***REDACTED***"
_MIN_VALUE_LEN = 4

SENSITIVE_KEYS = {
    "api_key", "apikey", "authorization", "access_token", "refresh_token",
    "client_secret", "password", "passwd", "secret", "token", "private_key",
    "vault_key", "master_key",
}

_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_\-]{10,}"),
    re.compile(r"(?i)(api[_-]?key\s*[:=]\s*)([A-Za-z0-9_\-]{8,})"),
    re.compile(r"(?i)(bearer\s+)([A-Za-z0-9_\-\.]{8,})"),
    re.compile(r"(?i)(password\s*[:=]\s*)(\S{4,})"),
    re.compile(r"(?i)(token\s*[:=]\s*)([A-Za-z0-9_\-\.]{8,})"),
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"ya29\.[A-Za-z0-9_\-]{20,}"),
]


class Redactor:
    def __init__(self) -> None:
        self._values: set[str] = set()

    def register(self, value: str | None) -> None:
        if isinstance(value, str) and len(value) >= _MIN_VALUE_LEN:
            self._values.add(value)

    def register_many(self, values) -> None:  # noqa: ANN001
        for value in values or []:
            self.register(value)

    def clear(self) -> None:
        self._values.clear()

    def redact_text(self, text: str) -> str:
        if not isinstance(text, str) or not text:
            return text
        out = text
        for value in sorted(self._values, key=len, reverse=True):
            if value and value in out:
                out = out.replace(value, PLACEHOLDER)
        for pattern in _PATTERNS:
            if pattern.groups >= 2:
                out = pattern.sub(lambda m: m.group(1) + PLACEHOLDER, out)
            else:
                out = pattern.sub(PLACEHOLDER, out)
        return out

    def redact_obj(self, obj: Any) -> Any:
        if isinstance(obj, dict):
            result: dict[Any, Any] = {}
            for key, val in obj.items():
                if isinstance(key, str) and key.lower() in SENSITIVE_KEYS:
                    result[key] = PLACEHOLDER
                else:
                    result[key] = self.redact_obj(val)
            return result
        if isinstance(obj, list):
            return [self.redact_obj(item) for item in obj]
        if isinstance(obj, tuple):
            return tuple(self.redact_obj(item) for item in obj)
        if isinstance(obj, str):
            return self.redact_text(obj)
        return obj


_DEFAULT = Redactor()


def get_default_redactor() -> Redactor:
    """Process-wide redactor the vault registers resolved secret values into."""
    return _DEFAULT


def redact_text(text: str) -> str:
    return _DEFAULT.redact_text(text)


def redact_obj(obj: Any) -> Any:
    return _DEFAULT.redact_obj(obj)
