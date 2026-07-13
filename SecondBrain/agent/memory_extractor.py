"""Extraction of governed memory candidates from source material.

The extractor turns raw text plus provenance into a :class:`MemoryCandidate`.
It never writes anything: its job is to describe *what could be remembered* and
attach everything the governance layer needs to decide - classification,
confidence, evidence, a sanitized preview and a stable deduplication key.

Two governance-relevant signals are computed here because only the extractor has
the surrounding context to judge them:

* ``contradicts`` - the candidate conflicts with an already-known fact.
* ``unsupported_preference`` - a stated personal preference with no evidence.

Both force human review downstream even when the content is otherwise benign.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Any, Iterable, Mapping, Sequence
from uuid import uuid4

from .memory_classification import ClassificationPolicy, ClassificationResult, DataClassification
from .privacy import PrivacyGuard, PrivacyMode

__all__ = [
    "MemoryCandidate",
    "MemoryExtractor",
    "DEFAULT_PREVIEW_LENGTH",
    "RETENTION_POLICIES",
    "detect_memory_secret",
    "redact_memory_secrets",
]

DEFAULT_PREVIEW_LENGTH = 160

# Retention policy -> lifetime in days (None == keep indefinitely).
RETENTION_POLICIES: dict[str, int | None] = {
    "ephemeral": 7,
    "short": 30,
    "standard": 365,
    "long": 365 * 3,
    "permanent": None,
}

_DEFAULT_CONFIDENCE = 0.75

_MEMORY_SECRET_PATTERNS = (
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


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class MemoryCandidate:
    """A proposed long-term memory, fully described for governance.

    ``content`` holds the raw text and is the only field that may contain
    sensitive material; it is never exposed to review previews or audit logs.
    Everything a reviewer or auditor sees comes from
    :attr:`content_preview`.
    """

    candidate_id: str
    memory_type: str
    content_preview: str
    source_id: str
    workspace_id: str
    evidence: tuple[dict[str, Any], ...]
    confidence: float
    classification: DataClassification
    retention_policy: str
    expires_at: str | None
    deduplication_key: str
    # Raw content is internal-only and omitted from review/audit persistence.
    content: str
    status: str = "pending"
    # Governance signals.
    source_trusted: bool = True
    contradicts: bool = False
    unsupported_preference: bool = False
    no_memory: bool = False
    created_at: str = field(default_factory=lambda: _utc_now().isoformat(timespec="seconds"))
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def has_evidence(self) -> bool:
        return bool(self.evidence)

    @property
    def sanitized_content_preview(self) -> str:
        """Backward-compatible alias for the safe review preview."""

        return self.content_preview

    @property
    def expiration(self) -> str | None:
        """Backward-compatible alias for ``expires_at``."""

        return self.expires_at

    def sanitized_dict(self) -> dict[str, Any]:
        """Representation safe to persist in reviews and audit - no raw content."""

        return {
            "candidate_id": self.candidate_id,
            "memory_type": self.memory_type,
            "content_preview": self.content_preview,
            "sanitized_content_preview": self.content_preview,
            "source_id": _sanitize_value(self.source_id, key="source_id"),
            "evidence": [_sanitize_value(dict(item)) for item in self.evidence],
            "confidence": self.confidence,
            "classification": self.classification.value,
            "workspace_id": self.workspace_id,
            "retention_policy": self.retention_policy,
            "expires_at": self.expires_at,
            "expiration": self.expires_at,
            "deduplication_key": self.deduplication_key,
            "status": self.status,
            "source_trusted": self.source_trusted,
            "contradicts": self.contradicts,
            "unsupported_preference": self.unsupported_preference,
            "no_memory": self.no_memory,
            "created_at": self.created_at,
        }


class MemoryExtractor:
    """Builds :class:`MemoryCandidate` objects from source text."""

    def __init__(
        self,
        *,
        classifier: ClassificationPolicy | None = None,
        preview_length: int = DEFAULT_PREVIEW_LENGTH,
        default_confidence: float = _DEFAULT_CONFIDENCE,
        privacy_mode: PrivacyMode = PrivacyMode.OFF,
    ) -> None:
        self._classifier = classifier or ClassificationPolicy()
        # Guard in OFF mode is used only to redact previews, never to block here.
        self._redactor = PrivacyGuard(PrivacyMode.OFF)
        self._privacy = PrivacyGuard(privacy_mode)
        self._preview_length = max(16, int(preview_length))
        self._default_confidence = _clamp(default_confidence)

    def extract(
        self,
        content: str,
        *,
        source_id: str,
        workspace_id: str = "",
        memory_type: str = "fact",
        confidence: float | None = None,
        evidence: Sequence[Mapping[str, Any]] | None = None,
        source_trusted: bool = True,
        no_memory: bool = False,
        retention_policy: str = "standard",
        known_facts: Iterable[Mapping[str, Any] | str] | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> MemoryCandidate:
        if self._privacy.mode != PrivacyMode.OFF:
            raise PermissionError("privacy_mode_active")
        text = (content or "").strip()
        if not text:
            raise ValueError("memory_candidate_content_required")
        if retention_policy not in RETENTION_POLICIES:
            raise ValueError(f"unknown_retention_policy:{retention_policy}")

        meta = dict(metadata or {})
        classification = self._classifier.classify(text, metadata=meta, source_id=source_id)
        normalized_evidence = _normalize_evidence(evidence)
        resolved_confidence = self._default_confidence if confidence is None else _clamp(confidence)

        unsupported_preference = memory_type.strip().lower() == "preference" and not normalized_evidence
        contradicts = self._contradicts(text, memory_type, known_facts)

        declared_no_memory = bool(no_memory) or _declared_no_memory(meta)
        secret_detected = classification.is_blocking or detect_memory_secret(text)
        return MemoryCandidate(
            candidate_id=str(uuid4()),
            memory_type=memory_type.strip().lower() or "fact",
            content_preview=self._sanitized_preview(text, classification),
            source_id=source_id,
            workspace_id=workspace_id,
            evidence=normalized_evidence,
            confidence=resolved_confidence,
            classification=classification.classification,
            retention_policy=retention_policy,
            expires_at=self._expiration(retention_policy),
            deduplication_key=_deduplication_key(memory_type, workspace_id, text),
            content=text,
            status="blocked" if declared_no_memory or secret_detected else "pending",
            source_trusted=bool(source_trusted),
            contradicts=contradicts,
            unsupported_preference=unsupported_preference,
            no_memory=declared_no_memory,
            metadata=meta,
        )

    def _sanitized_preview(self, text: str, classification: ClassificationResult) -> str:
        if detect_memory_secret(text):
            return "[REDACTED_SECRET]"
        redacted = self._redactor.inspect_memory_write(text).redacted_text or text
        # Credentials/secrets must never surface even truncated.
        if classification.is_secret or classification.classification == DataClassification.CREDENTIAL:
            return "[REDACTED_SECRET]"
        collapsed = re.sub(r"\s+", " ", redacted).strip()
        if len(collapsed) <= self._preview_length:
            return collapsed
        return collapsed[: self._preview_length - 1].rstrip() + "…"

    @staticmethod
    def _expiration(retention_policy: str) -> str | None:
        days = RETENTION_POLICIES[retention_policy]
        if days is None:
            return None
        return (_utc_now() + timedelta(days=days)).isoformat(timespec="seconds")

    @staticmethod
    def _contradicts(
        text: str,
        memory_type: str,
        known_facts: Iterable[Mapping[str, Any] | str] | None,
    ) -> bool:
        if not known_facts:
            return False
        subject = _subject_key(text)
        if not subject:
            return False
        normalized_text = _normalize(text)
        for fact in known_facts:
            fact_text = fact if isinstance(fact, str) else str(fact.get("text") or fact.get("content") or "")
            if not fact_text:
                continue
            if _subject_key(fact_text) != subject:
                continue
            # Same subject, materially different statement -> contradiction.
            if _normalize(fact_text) != normalized_text:
                return True
        return False


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _subject_key(text: str) -> str:
    """First few significant tokens - a cheap subject fingerprint."""

    tokens = re.findall(r"[\wäöüß]+", (text or "").lower())
    stop = {"ist", "war", "the", "a", "der", "die", "das", "is", "are", "of", "und", "and"}
    significant = [token for token in tokens if token not in stop]
    return " ".join(significant[:3])


def _deduplication_key(memory_type: str, workspace_id: str, text: str) -> str:
    raw = "|".join([memory_type.strip().lower(), workspace_id or "", _normalize(text)])
    return sha256(raw.encode("utf-8")).hexdigest()[:32]


def _normalize_evidence(evidence: Sequence[Mapping[str, Any]] | None) -> tuple[dict[str, Any], ...]:
    if not evidence:
        return ()
    normalized: list[dict[str, Any]] = []
    for item in evidence:
        if isinstance(item, Mapping):
            normalized.append({str(k): v for k, v in item.items()})
        else:  # tolerate bare strings as source references
            normalized.append({"source": str(item)})
    return tuple(normalized)


def _sanitize_value(value: Any, *, key: str = "") -> Any:
    """Redact secret-bearing evidence before review or audit serialization."""

    normalized_key = re.sub(r"[^a-z0-9]", "", key.lower())
    if key and any(marker in normalized_key for marker in (
        "apikey", "credential", "password", "passwd", "privatekey", "secret", "token",
    )):
        return "***"
    if isinstance(value, Mapping):
        return {str(item_key): _sanitize_value(item, key=str(item_key)) for item_key, item in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_sanitize_value(item) for item in value]
    if isinstance(value, str):
        if detect_memory_secret(value):
            return redact_memory_secrets(value)
        result = PrivacyGuard(PrivacyMode.OFF).inspect_memory_write(value)
        return result.redacted_text if result.reason == "secret_redacted" else value
    return value


def detect_memory_secret(text: str) -> bool:
    return any(pattern.search(text or "") for pattern in _MEMORY_SECRET_PATTERNS)


def redact_memory_secrets(text: str) -> str:
    redacted = text or ""
    for pattern in _MEMORY_SECRET_PATTERNS:
        redacted = pattern.sub("[REDACTED_SECRET]", redacted)
    return redacted


def _declared_no_memory(metadata: Mapping[str, Any]) -> bool:
    for key in ("no_memory", "do_not_remember", "ephemeral_only"):
        if bool(metadata.get(key)):
            return True
    tags = metadata.get("tags")
    if isinstance(tags, (list, tuple, set)) and "no_memory" in {str(tag).lower() for tag in tags}:
        return True
    return False
