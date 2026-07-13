from secondbrain.document_understanding.orchestrator import ParseOrchestrationResult, ParserSelection
from secondbrain.document_understanding.parser_contract import ParseStatus, build_parsed_document
from secondbrain.document_understanding.quality_gate import (
    IngestionQualityGate,
    QualityDecision,
    QualityGatePolicy,
    RejectReason,
    ReviewReason,
)


def test_quality_gate_accepts_valid_parsed_document():
    parsed = build_parsed_document(
        title="Valid",
        text="This document contains enough normalized words for ingestion.",
        mime_type="text/plain",
    )

    result = IngestionQualityGate().evaluate(parsed)

    assert result.ok is True
    assert result.decision in {QualityDecision.ACCEPT, QualityDecision.REVIEW}
    assert result.reject_reasons == ()
    assert result.metrics["chars"] >= 20


def test_quality_gate_rejects_ocr_required_document():
    parsed = build_parsed_document(
        title="Scan.pdf",
        text="",
        mime_type="application/pdf",
        status=ParseStatus.OCR_REQUIRED,
        errors=["pdf_has_no_extractable_text"],
    )

    result = IngestionQualityGate().evaluate(parsed)

    assert result.ok is False
    assert result.decision == QualityDecision.REJECT
    assert RejectReason.OCR_REQUIRED in result.reject_reasons
    assert RejectReason.EMPTY_CONTENT in result.reject_reasons


def test_quality_gate_rejects_too_short_content():
    parsed = build_parsed_document(title="Tiny", text="hi", mime_type="text/plain")

    result = IngestionQualityGate().evaluate(parsed)

    assert result.ok is False
    assert RejectReason.BELOW_MIN_CHARS in result.reject_reasons
    assert RejectReason.BELOW_MIN_WORDS in result.reject_reasons


def test_quality_gate_supports_allowed_mime_policy():
    parsed = build_parsed_document(
        title="Data",
        text="Valid content with enough words for the quality gate.",
        mime_type="application/json",
    )
    gate = IngestionQualityGate(QualityGatePolicy(allowed_mime_types=frozenset({"text/plain"})))

    result = gate.evaluate(parsed)

    assert result.ok is False
    assert RejectReason.DISALLOWED_MIME_TYPE in result.reject_reasons


def test_quality_gate_marks_orchestration_warnings_for_review():
    parsed = build_parsed_document(
        title="Short",
        text="Short but valid content for review path.",
        mime_type="text/plain",
    )
    orchestration = ParseOrchestrationResult(
        parsed=parsed,
        selection=ParserSelection("PlainTextParser", ".txt", "text/plain", "extension"),
        warnings=("very_short_text",),
    )

    result = IngestionQualityGate(QualityGatePolicy(min_chars=10, min_words=3)).evaluate(orchestration)

    assert result.ok is True
    assert result.decision == QualityDecision.REVIEW
    assert ReviewReason.PARSER_WARNINGS in result.review_reasons
