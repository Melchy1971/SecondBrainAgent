"""P1.3.5 - Ingestion quality gate for parsed documents.

The quality gate is the last deterministic check before parsed content is handed
into ingestion, chunking, or indexing. It converts parser states and weak content
signals into explicit accept/reject decisions with machine-readable reasons.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from .orchestrator import ParseOrchestrationResult
from .parser_contract import ParsedDocument, ParseStatus, normalize_text


class QualityDecision(str, Enum):
    """Stable quality-gate decisions used by ingestion and release checks."""

    ACCEPT = "accept"
    REJECT = "reject"
    REVIEW = "review"


class RejectReason(str, Enum):
    """Machine-readable reasons for rejected parsed documents."""

    PARSER_FAILED = "parser_failed"
    UNSUPPORTED_TYPE = "unsupported_type"
    OCR_REQUIRED = "ocr_required"
    EMPTY_CONTENT = "empty_content"
    BELOW_MIN_CHARS = "below_min_chars"
    BELOW_MIN_WORDS = "below_min_words"
    MISSING_TITLE = "missing_title"
    MISSING_MIME_TYPE = "missing_mime_type"
    SOURCE_PATH_MISMATCH = "source_path_mismatch"
    DISALLOWED_MIME_TYPE = "disallowed_mime_type"


class ReviewReason(str, Enum):
    """Non-blocking quality signals that should be visible to operators."""

    VERY_SHORT_CONTENT = "very_short_content"
    NO_PAGE_BOUNDARIES = "no_page_boundaries"
    PARSER_WARNINGS = "parser_warnings"
    NO_SOURCE_PATH = "no_source_path"


@dataclass(frozen=True, slots=True)
class QualityGatePolicy:
    """Configurable thresholds for parsed-document quality."""

    min_chars: int = 20
    min_words: int = 3
    review_below_chars: int = 40
    require_title: bool = True
    require_mime_type: bool = True
    require_existing_source_path: bool = False
    allowed_mime_types: frozenset[str] = field(default_factory=frozenset)


@dataclass(frozen=True, slots=True)
class QualityGateResult:
    """Quality decision with enough context for logs, UI, and tests."""

    decision: QualityDecision
    parsed_status: ParseStatus
    accepted: bool
    reject_reasons: tuple[RejectReason, ...] = ()
    review_reasons: tuple[ReviewReason, ...] = ()
    metrics: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.accepted

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "decision": self.decision.value,
            "parsed_status": self.parsed_status.value,
            "reject_reasons": [reason.value for reason in self.reject_reasons],
            "review_reasons": [reason.value for reason in self.review_reasons],
            "metrics": dict(self.metrics),
            "metadata": dict(self.metadata),
        }


class IngestionQualityGate:
    """Validate parser results before ingestion/indexing side effects happen."""

    def __init__(self, policy: QualityGatePolicy | None = None) -> None:
        self.policy = policy or QualityGatePolicy()

    def evaluate(self, value: ParsedDocument | ParseOrchestrationResult) -> QualityGateResult:
        parsed, orchestration_warnings = _unwrap(value)
        text = normalize_text(parsed.text)
        words = _word_count(text)
        title = (parsed.title or "").strip()
        mime_type = (parsed.mime_type or "").strip().lower()

        reject_reasons: list[RejectReason] = []
        review_reasons: list[ReviewReason] = []

        if parsed.status == ParseStatus.FAILED:
            reject_reasons.append(RejectReason.PARSER_FAILED)
        elif parsed.status == ParseStatus.UNSUPPORTED:
            reject_reasons.append(RejectReason.UNSUPPORTED_TYPE)
        elif parsed.status == ParseStatus.OCR_REQUIRED:
            reject_reasons.append(RejectReason.OCR_REQUIRED)
        elif parsed.status == ParseStatus.EMPTY:
            reject_reasons.append(RejectReason.EMPTY_CONTENT)
        elif parsed.status != ParseStatus.PARSED:
            reject_reasons.append(RejectReason.PARSER_FAILED)

        if not text:
            _append_unique(reject_reasons, RejectReason.EMPTY_CONTENT)
        if len(text) < self.policy.min_chars:
            _append_unique(reject_reasons, RejectReason.BELOW_MIN_CHARS)
        if words < self.policy.min_words:
            _append_unique(reject_reasons, RejectReason.BELOW_MIN_WORDS)
        if self.policy.require_title and not title:
            reject_reasons.append(RejectReason.MISSING_TITLE)
        if self.policy.require_mime_type and not mime_type:
            reject_reasons.append(RejectReason.MISSING_MIME_TYPE)
        if self.policy.allowed_mime_types and mime_type not in self.policy.allowed_mime_types:
            reject_reasons.append(RejectReason.DISALLOWED_MIME_TYPE)
        if self.policy.require_existing_source_path and parsed.source_path:
            if not Path(parsed.source_path).exists():
                reject_reasons.append(RejectReason.SOURCE_PATH_MISMATCH)

        if not reject_reasons:
            if len(text) < self.policy.review_below_chars:
                review_reasons.append(ReviewReason.VERY_SHORT_CONTENT)
            if parsed.page_count == 0 and mime_type == "application/pdf":
                review_reasons.append(ReviewReason.NO_PAGE_BOUNDARIES)
            if orchestration_warnings:
                review_reasons.append(ReviewReason.PARSER_WARNINGS)
            if not parsed.source_path:
                review_reasons.append(ReviewReason.NO_SOURCE_PATH)

        decision = QualityDecision.ACCEPT
        if reject_reasons:
            decision = QualityDecision.REJECT
        elif review_reasons:
            decision = QualityDecision.REVIEW

        return QualityGateResult(
            decision=decision,
            parsed_status=parsed.status,
            accepted=not reject_reasons,
            reject_reasons=tuple(reject_reasons),
            review_reasons=tuple(review_reasons),
            metrics={
                "chars": len(text),
                "words": words,
                "pages": parsed.page_count,
                "errors": len(parsed.errors),
                "warnings": len(orchestration_warnings),
            },
            metadata={
                "title": title,
                "mime_type": mime_type,
                "source_path": parsed.source_path,
            },
        )


def _unwrap(value: ParsedDocument | ParseOrchestrationResult) -> tuple[ParsedDocument, tuple[str, ...]]:
    if isinstance(value, ParseOrchestrationResult):
        return value.parsed, tuple(value.warnings)
    return value, ()


def _word_count(text: str) -> int:
    return len([part for part in text.split(" ") if part.strip()])


def _append_unique(items: list[RejectReason], item: RejectReason) -> None:
    if item not in items:
        items.append(item)
