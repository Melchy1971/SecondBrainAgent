"""Redaction so secrets never appear in logs or serialized output."""

from __future__ import annotations

import logging
import re

MASK = "***REDACTED***"
# common secret-looking patterns as a defense-in-depth net
_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|secret|token|password|passwd|bearer)\s*[=:]\s*\S+"),
    re.compile(r"sk-[A-Za-z0-9]{16,}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{5,}"),  # JWT
]


def redact_text(text: str, *, known_values: list[str] | None = None) -> str:
    out = text
    for value in known_values or []:
        if value:
            out = out.replace(value, MASK)
    for pat in _PATTERNS:
        out = pat.sub(lambda m: _mask_pair(m.group(0)), out)
    return out


def _mask_pair(fragment: str) -> str:
    if "=" in fragment or ":" in fragment:
        sep = "=" if "=" in fragment else ":"
        head = fragment.split(sep, 1)[0]
        return f"{head}{sep}{MASK}"
    return MASK


def redact_mapping(data: dict, *, sensitive_keys=("value", "secret", "token", "api_key", "password")) -> dict:
    out = {}
    for k, v in data.items():
        if any(s in str(k).lower() for s in sensitive_keys):
            out[k] = MASK
        elif isinstance(v, dict):
            out[k] = redact_mapping(v, sensitive_keys=sensitive_keys)
        else:
            out[k] = v
    return out


class SecretRedactingFilter(logging.Filter):
    """Logging filter that scrubs secret-looking content from log records."""

    def __init__(self, known_values: list[str] | None = None) -> None:
        super().__init__()
        self.known_values = known_values or []

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            record.msg = redact_text(str(record.getMessage()), known_values=self.known_values)
            record.args = ()
        except Exception:
            pass
        return True
