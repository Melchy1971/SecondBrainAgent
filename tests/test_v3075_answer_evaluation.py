from __future__ import annotations

from pathlib import Path

from secondbrain.chat import AnswerEvaluator
from secondbrain.chat.evaluation import EvidenceRater, HallucinationDetector, SourceVerifier
from secondbrain.native.chat import ChatEngine
from secondbrain.providers.base.provider_models import CompletionResponse


EVIDENCE = [{
    "document_id": "doc-1",
    "chunk_id": "chunk-1",
    "title": "Geography",
    "source": "reference.md",
    "text": "Paris is the capital of France. The official population is 2 million.",
    "score": 0.95,
    "source_trust": 0.9,
}]

CITATIONS = [{
    "document": "Geography",
    "document_id": "doc-1",
    "chunk": "chunk-1",
    "source": "reference.md",
}]


def test_grounded_answer_gets_verified_sources_and_high_confidence() -> None:
    result = AnswerEvaluator().evaluate(
        "What is the capital of France?",
        "Paris is the capital of France.",
        evidence=EVIDENCE,
        citations=CITATIONS,
    )

    assert result.hallucination.detected is False
    assert result.source_verification.score == 1.0
    assert result.evidence_rating.usable_count == 1
    assert result.answer_rating.score >= 90
    assert result.confidence.level == "high"
    assert result.confidence.score >= 0.9


def test_hallucination_detection_flags_unsupported_entity_and_number() -> None:
    result = HallucinationDetector().detect(
        "Berlin is the capital of France. The population is 9 million.",
        EVIDENCE,
    )

    assert result.detected is True
    assert result.claim_count == 2
    assert len(result.unsupported_claims) == 2
    assert {row.reason for row in result.unsupported_claims} == {
        "insufficient_evidence_overlap",
        "unsupported_numeric_claim",
    }
    numeric = next(row for row in result.unsupported_claims if row.reason == "unsupported_numeric_claim")
    assert numeric.unsupported_numbers == ("9",)


def test_citation_markers_are_not_numeric_claims_and_empty_answer_is_not_grounded() -> None:
    detector = HallucinationDetector()
    cited = detector.detect("Paris is the capital of France [1].", EVIDENCE)
    empty = detector.detect("", EVIDENCE)

    assert cited.detected is False
    assert empty.claim_count == 0
    assert empty.groundedness == 0.0


def test_source_verification_requires_matching_strong_identifier() -> None:
    verifier = SourceVerifier()
    valid = verifier.verify(CITATIONS, EVIDENCE)
    invalid = verifier.verify([{**CITATIONS[0], "chunk": "missing"}], EVIDENCE)

    assert valid.score == 1.0
    assert valid.checks[0].evidence_id == "chunk-1"
    assert invalid.score == 0.0
    assert invalid.checks[0].reason == "source_not_found"


def test_evidence_rating_scores_relevance_source_and_completeness() -> None:
    rating = EvidenceRater().rate(
        "capital France",
        "Paris is the capital of France",
        [*EVIDENCE, {"id": "weak", "text": "unrelated", "score": 0.1}],
    )

    assert rating.usable_count == 2
    assert rating.items[0].evidence_id == "chunk-1"
    assert rating.items[0].score > rating.items[1].score
    assert 0.0 <= rating.score <= 1.0


def test_no_evidence_produces_low_rating_critique_and_suggestions() -> None:
    result = AnswerEvaluator().evaluate(
        "What is the release status?",
        "The release status is green.",
    )
    payload = result.to_dict()

    assert result.hallucination.detected is True
    assert result.source_verification.score == 0.0
    assert result.evidence_rating.usable_count == 0
    assert result.answer_rating.score < 50
    assert result.confidence.level == "low"
    assert result.self_critique.weaknesses
    assert len(result.improvement_suggestions) >= 2
    assert payload["answer_rating"]["score"] == result.answer_rating.score


def test_partial_grounding_exposes_public_self_critique_not_hidden_reasoning() -> None:
    result = AnswerEvaluator().evaluate(
        "What is the capital and population?",
        "Paris is the capital of France. The population is 9 million.",
        evidence=EVIDENCE,
        citations=CITATIONS,
    )

    assert result.hallucination.detected is True
    assert result.self_critique.strengths
    assert result.self_critique.weaknesses
    assert any("unsupported" in suggestion for suggestion in result.improvement_suggestions)
    assert "chain_of_thought" not in result.to_dict()


class _Provider:
    def complete(self, provider: str, request):
        return CompletionResponse(provider=provider, model=request.model, content="Paris is the capital of France.")


class _Rag:
    def hybrid_search(self, query: str, limit: int = 5):
        return {"hits": EVIDENCE}


class _Memory:
    def search(self, query: str, limit: int = 5):
        return {"memories": []}


def test_chat_engine_attaches_evaluation_to_result_and_message(tmp_path: Path) -> None:
    engine = ChatEngine(tmp_path, provider_manager=_Provider(), rag_runtime=_Rag(), memory_explorer=_Memory())
    result = engine.send("What is the capital of France?", provider="test", model="m")

    assert result["evaluation"]["confidence"]["level"] == "high"
    messages = engine.conversations.messages(result["conversation"]["id"])
    assert messages[-1]["metadata"]["evaluation"] == result["evaluation"]
