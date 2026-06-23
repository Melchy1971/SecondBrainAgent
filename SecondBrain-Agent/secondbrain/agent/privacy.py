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
        re.compile(r"(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*[^\s]+"),
        re.compile(r"sk-[A-Za-z0-9_-]{12,}"),
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
