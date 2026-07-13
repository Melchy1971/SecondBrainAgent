from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
import re
from typing import Any


class PrivacyMode(StrEnum):
    OFF = "off"
    RESTRICTED = "restricted"
    STRICT = "strict"


class PrivacyDecision(StrEnum):
    ALLOW = "allow"
    REDACT = "redact"
    BLOCK = "block"


@dataclass(frozen=True)
class PrivacyRuleResult:
    decision: PrivacyDecision
    reason: str
    redacted_text: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class PrivacyGuard:
    SECRET_PATTERNS = (
        re.compile(
            r"-----BEGIN(?: [A-Z0-9]+)? PRIVATE KEY-----.*?"
            r"-----END(?: [A-Z0-9]+)? PRIVATE KEY-----",
            re.IGNORECASE | re.DOTALL,
        ),
        re.compile(r"-----BEGIN(?: [A-Z0-9]+)? PRIVATE KEY-----[\s\S]*", re.IGNORECASE),
        re.compile(
            r"(?i)\b(api[\s_-]?key|access[_-]?token|auth[_-]?token|token|secret|"
            r"client[_-]?secret|password|passwd|credential(?:s)?)\s*[:=]\s*[^\s,;]+"
        ),
        re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/-]+=*"),
        re.compile(r"sk-[A-Za-z0-9_-]{12,}"),
        re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
        re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    )

    def __init__(self, mode: PrivacyMode = PrivacyMode.OFF) -> None:
        self.mode = mode

    def inspect_memory_write(self, text: str, *, metadata: dict[str, Any] | None = None) -> PrivacyRuleResult:
        if self.mode == PrivacyMode.STRICT:
            return PrivacyRuleResult(PrivacyDecision.BLOCK, "privacy_mode_strict")
        redacted = text
        found_secret = False
        for pattern in self.SECRET_PATTERNS:
            if pattern.search(redacted):
                found_secret = True
                redacted = pattern.sub("[REDACTED_SECRET]", redacted)
        if found_secret:
            if self.mode == PrivacyMode.RESTRICTED:
                return PrivacyRuleResult(PrivacyDecision.REDACT, "secret_redacted", redacted_text=redacted)
            return PrivacyRuleResult(PrivacyDecision.REDACT, "secret_redacted", redacted_text=redacted)
        return PrivacyRuleResult(PrivacyDecision.ALLOW, "allowed", redacted_text=text)

    def require_memory_allowed(self, text: str) -> str:
        result = self.inspect_memory_write(text)
        if result.decision == PrivacyDecision.BLOCK:
            raise PermissionError(result.reason)
        return result.redacted_text or text
