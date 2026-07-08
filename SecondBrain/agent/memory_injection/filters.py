"""v30.64 Agent Memory Injection - secret & privacy filters, source rule.

Two hard gates the injector always applies:
* ``is_secret`` - secrets are NEVER injected, regardless of query or mode.
* ``privacy_excluded`` - in privacy mode, private/personal memories are withheld.

Plus the source rule (Quellenpflicht): every injected memory carries a source.
"""

from __future__ import annotations

import re

# Substten of the production audit's sensitive keys, plus injection-specific ones.
SECRET_METADATA_KEYS = {"password", "token", "secret", "api_key", "apikey",
                        "credential", "credentials", "private_key", "access_key"}
SECRET_TAGS = {"secret", "password", "token", "api_key", "credential", "private_key"}

# Value patterns that strongly indicate a leaked secret in the text itself.
SECRET_PATTERNS = [
    re.compile(r"\bsk-[A-Za-z0-9]{16,}\b"),              # OpenAI-style keys
    re.compile(r"\bAKIA[0-9A-Z]{12,}\b"),                # AWS access key id
    re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"),             # GitHub token
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),   # PEM private key
    re.compile(r"(?i)\b(password|passwort|api[_-]?key|secret|token)\s*[:=]\s*\S+"),
    re.compile(r"\b[A-Fa-f0-9]{32,}\b"),                 # long hex blob
]

# Privacy-mode exclusions.
PRIVATE_TAGS = {"private", "personal", "sensitive", "confidential", "privat", "persoenlich"}


def is_secret(record) -> tuple[bool, str]:
    metadata = getattr(record, "metadata", {}) or {}
    if metadata.get("secret") is True or metadata.get("is_secret") is True:
        return True, "metadata_flag"
    lowered_keys = {str(k).lower() for k in metadata.keys()}
    hit = lowered_keys & SECRET_METADATA_KEYS
    if hit:
        return True, f"metadata_key:{sorted(hit)[0]}"
    tags = {str(t).lower() for t in getattr(record, "tags", ())}
    tag_hit = tags & SECRET_TAGS
    if tag_hit:
        return True, f"tag:{sorted(tag_hit)[0]}"
    text = getattr(record, "text", "") or ""
    for pattern in SECRET_PATTERNS:
        if pattern.search(text):
            return True, "text_pattern"
    return False, ""


def privacy_excluded(record, privacy_mode: bool) -> tuple[bool, str]:
    if not privacy_mode:
        return False, ""
    metadata = getattr(record, "metadata", {}) or {}
    if metadata.get("private") is True or metadata.get("personal") is True:
        return True, "metadata_private"
    visibility = str(getattr(getattr(record, "visibility", ""), "value",
                             getattr(record, "visibility", ""))).lower()
    if visibility == "private":
        return True, "visibility_private"
    tags = {str(t).lower() for t in getattr(record, "tags", ())}
    tag_hit = tags & PRIVATE_TAGS
    if tag_hit:
        return True, f"tag:{sorted(tag_hit)[0]}"
    return False, ""


def source_of(record) -> str:
    metadata = getattr(record, "metadata", {}) or {}
    src = metadata.get("source")
    if src:
        return str(src)
    return f"memory:{str(getattr(record, 'memory_id', ''))[:8]}"


def has_explicit_source(record) -> bool:
    metadata = getattr(record, "metadata", {}) or {}
    return bool(metadata.get("source"))
