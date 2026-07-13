"""Data classification and privacy policy for governed memory writes.

This module answers a single question about a piece of candidate memory content:
*how sensitive is it, and must a human decide before it enters long-term memory?*

It deliberately owns no storage. Detection is pattern based and conservative:
when in doubt it escalates to the more sensitive class, because a false review
is cheap while a leaked secret or health record is not.

The secret/credential detection reuses :class:`secondbrain.agent.privacy.PrivacyGuard`
so there is exactly one definition of "this looks like a secret" in the codebase.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Mapping

from .privacy import PrivacyDecision, PrivacyGuard, PrivacyMode

__all__ = [
    "DataClassification",
    "ClassificationResult",
    "ClassificationPolicy",
    "REVIEW_REQUIRED_CLASSIFICATIONS",
    "BLOCKING_CLASSIFICATIONS",
]


class DataClassification(StrEnum):
    """Sensitivity classes ordered from least to most restrictive.

    Ordering matters: :meth:`ClassificationPolicy.classify` returns the most
    sensitive class that matches, using :data:`_SENSITIVITY_ORDER`.
    """

    PUBLIC = "public"
    INTERNAL = "internal"
    PERSONAL = "personal"
    PRIVATE_COMMUNICATION = "private_communication"
    SENSITIVE_PERSONAL = "sensitive_personal"
    FINANCIAL = "financial"
    HEALTH = "health"
    CREDENTIAL = "credential"


# Higher index == more sensitive. Used to pick the dominant class on multi-match.
_SENSITIVITY_ORDER: tuple[DataClassification, ...] = (
    DataClassification.PUBLIC,
    DataClassification.INTERNAL,
    DataClassification.PERSONAL,
    DataClassification.PRIVATE_COMMUNICATION,
    DataClassification.SENSITIVE_PERSONAL,
    DataClassification.FINANCIAL,
    DataClassification.HEALTH,
    DataClassification.CREDENTIAL,
)

# Classes that must never be auto-written and are hard-blocked.
BLOCKING_CLASSIFICATIONS: frozenset[DataClassification] = frozenset(
    {DataClassification.CREDENTIAL}
)

# Classes that require human review before entering long-term memory.
REVIEW_REQUIRED_CLASSIFICATIONS: frozenset[DataClassification] = frozenset(
    {
        DataClassification.PRIVATE_COMMUNICATION,
        DataClassification.SENSITIVE_PERSONAL,
        DataClassification.FINANCIAL,
        DataClassification.HEALTH,
    }
)


@dataclass(frozen=True)
class ClassificationResult:
    classification: DataClassification
    matched: tuple[DataClassification, ...] = ()
    is_secret: bool = False
    reason: str = ""

    @property
    def requires_review(self) -> bool:
        return self.classification in REVIEW_REQUIRED_CLASSIFICATIONS

    @property
    def is_blocking(self) -> bool:
        return self.is_secret or self.classification in BLOCKING_CLASSIFICATIONS

    def to_dict(self) -> dict[str, Any]:
        return {
            "classification": self.classification.value,
            "matched": [item.value for item in self.matched],
            "is_secret": self.is_secret,
            "reason": self.reason,
        }


# Keyword and structural patterns. German + English, because the vault is bilingual.
_HEALTH_PATTERNS = (
    re.compile(
        r"(?i)\b(diagnos(?:e|is|ed)|krankheit|erkrankung|symptom|therapie|therapy|"
        r"medikament|medication|dosis|dosage|blutdruck|blood pressure|"
        r"depression|angststörung|hiv|krebs|cancer|schwanger|pregnan|"
        r"psychiatr|arztbrief|befund|rezept|prescription)\b"
    ),
)
_FINANCIAL_PATTERNS = (
    re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{10,30}\b"),  # IBAN-like
    re.compile(r"\b(?:\d[ -]?){13,19}\b"),  # card-number-like
    re.compile(
        r"(?i)\b(gehalt|salary|kontostand|account balance|kreditkarte|credit card|"
        r"steuernummer|tax id|umsatz|iban|bic|einkommen|income|schulden|debt)\b"
    ),
)
_SENSITIVE_PERSONAL_PATTERNS = (
    re.compile(
        r"(?i)(religi|konfession|ethni|herkunft|\brace\b|sexuell|sexual orientation|"
        r"homosexuell|politisch|political affiliation|gewerkschaft|union member|"
        r"personalausweis|sozialversicherungsnummer|social security|\bssn\b|"
        r"passnummer|passport number|vorstrafe|criminal record)"
    ),
)
_PRIVATE_COMMUNICATION_PATTERNS = (
    re.compile(
        r"(?i)\b(private nachricht|privatnachricht|private message|persönliche nachricht|"
        r"whatsapp|direktnachricht|direct message|\bdm\b|vertraulich zwischen|"
        r"unter uns|between us|off the record)\b"
    ),
)
# Source identifiers that imply private one-to-one communication.
_PRIVATE_SOURCE_HINTS = (
    "whatsapp",
    "signal",
    "telegram",
    "dm",
    "direct_message",
    "private_message",
    "privatchat",
)


class ClassificationPolicy:
    """Classifies free text into a :class:`DataClassification`."""

    def __init__(self, privacy_guard: PrivacyGuard | None = None) -> None:
        # A guard in OFF mode only performs detection, never blocking/redaction
        # side effects - classification stays independent of the active mode.
        self._detector = privacy_guard or PrivacyGuard(PrivacyMode.OFF)

    def detect_secret(self, text: str) -> bool:
        result = self._detector.inspect_memory_write(text or "")
        return result.decision != PrivacyDecision.ALLOW and result.reason == "secret_redacted"

    def classify(
        self,
        text: str,
        *,
        metadata: Mapping[str, Any] | None = None,
        source_id: str = "",
    ) -> ClassificationResult:
        content = text or ""
        matched: list[DataClassification] = []

        is_secret = self.detect_secret(content)
        if is_secret:
            matched.append(DataClassification.CREDENTIAL)

        if self._any(content, _HEALTH_PATTERNS):
            matched.append(DataClassification.HEALTH)
        if self._any(content, _FINANCIAL_PATTERNS):
            matched.append(DataClassification.FINANCIAL)
        if self._any(content, _SENSITIVE_PERSONAL_PATTERNS):
            matched.append(DataClassification.SENSITIVE_PERSONAL)
        if self._is_private_communication(content, metadata=metadata, source_id=source_id):
            matched.append(DataClassification.PRIVATE_COMMUNICATION)

        declared = self._declared(metadata)
        if declared is not None:
            matched.append(declared)

        if not matched:
            baseline = DataClassification.PERSONAL if self._looks_personal(content) else DataClassification.INTERNAL
            return ClassificationResult(
                classification=baseline,
                matched=(),
                is_secret=False,
                reason="no_sensitive_pattern",
            )

        dominant = max(matched, key=_SENSITIVITY_ORDER.index)
        return ClassificationResult(
            classification=dominant,
            matched=tuple(dict.fromkeys(matched)),
            is_secret=is_secret,
            reason="pattern_match",
        )

    @staticmethod
    def _any(text: str, patterns: tuple[re.Pattern[str], ...]) -> bool:
        return any(pattern.search(text) for pattern in patterns)

    def _is_private_communication(
        self,
        text: str,
        *,
        metadata: Mapping[str, Any] | None,
        source_id: str,
    ) -> bool:
        if self._any(text, _PRIVATE_COMMUNICATION_PATTERNS):
            return True
        haystack = f"{source_id} {(metadata or {}).get('source', '')} {(metadata or {}).get('channel', '')}".lower()
        return any(hint in haystack for hint in _PRIVATE_SOURCE_HINTS)

    @staticmethod
    def _declared(metadata: Mapping[str, Any] | None) -> DataClassification | None:
        if not metadata:
            return None
        raw = str(metadata.get("classification") or metadata.get("data_classification") or "").strip().lower()
        if not raw:
            return None
        try:
            return DataClassification(raw)
        except ValueError:
            return None

    @staticmethod
    def _looks_personal(text: str) -> bool:
        return bool(re.search(r"(?i)\b(ich|mein|meine|my|i am|i'm|persönlich|personal)\b", text))