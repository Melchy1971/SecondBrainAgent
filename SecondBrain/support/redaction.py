"""Recursive secret/PII redaction for support bundles.

Two layers of defence:
  * key-based: any mapping key that looks sensitive (password, token, api_key,
    database_url, ...) has its value replaced regardless of content;
  * value-based: any string is scanned for secret-shaped substrings
    (PEM keys, ``key=value`` secrets, bearer tokens, sk-/gh_/AKIA tokens) and
    those substrings are replaced.

Everything a support bundle emits passes through :func:`redact` so an exported
ZIP never contains live credentials.
"""

from __future__ import annotations

import re
from typing import Any, Mapping

__all__ = ["REDACTED", "redact", "redact_text", "redact_env", "is_sensitive_key"]

REDACTED = "[REDACTED]"

_SENSITIVE_KEY_TOKENS = (
    "password", "passwd", "secret", "token", "api_key", "apikey", "api-key",
    "authorization", "auth_token", "access_key", "access-key", "client_secret",
    "private_key", "privatekey", "credential", "cookie", "session", "dsn",
    "database_url", "connection_string", "conn_str", "sas_token", "refresh_token",
)

_SECRET_PATTERNS = (
    re.compile(r"-----BEGIN(?: [A-Z0-9]+)? PRIVATE KEY-----[\s\S]*?-----END(?: [A-Z0-9]+)? PRIVATE KEY-----", re.IGNORECASE),
    re.compile(r"-----BEGIN(?: [A-Z0-9]+)? PRIVATE KEY-----[\s\S]*", re.IGNORECASE),
    re.compile(
        r"(?i)[\w.\-]*(?:api[\s_-]?key|apikey|access[_-]?token|auth[_-]?token|refresh[_-]?token|token|secret|"
        r"client[_-]?secret|password|passwd|credential(?:s)?)\s*[:=]\s*[^\s,;\"']+"
    ),
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/-]+=*"),
    re.compile(r"sk-[A-Za-z0-9_-]{12,}"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    # postgres/redis style URLs with credentials -> mask the user:pass part
    re.compile(r"(?i)\b([a-z][a-z0-9+.\-]*://)[^:/@\s]+:[^@/\s]+@"),
)


def is_sensitive_key(key: str) -> bool:
    k = str(key).lower()
    return any(token in k for token in _SENSITIVE_KEY_TOKENS)


def redact_text(value: str) -> str:
    text = value
    for i, pattern in enumerate(_SECRET_PATTERNS):
        if i == len(_SECRET_PATTERNS) - 1:
            # URL credential pattern keeps the scheme, masks user:pass@
            text = pattern.sub(lambda m: f"{m.group(1)}{REDACTED}@", text)
        else:
            text = pattern.sub(REDACTED, text)
    return text


def redact(value: Any, *, key: str = "") -> Any:
    if key and is_sensitive_key(key):
        return REDACTED
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, Mapping):
        return {k: redact(v, key=str(k)) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [redact(item) for item in value]
    return value


def redact_env(environ: Mapping[str, str]) -> dict[str, str]:
    """Keep variable names, mask sensitive values (so the bundle shows *which*
    variables are set without leaking their contents)."""

    out: dict[str, str] = {}
    for name, val in environ.items():
        if is_sensitive_key(name):
            out[name] = REDACTED if val else ""
        else:
            out[name] = redact_text(str(val))
    return out
