"""v30.75 grounded, deterministic evaluation of chat answers."""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any, Iterable, Mapping

from secondbrain.agent.reasoning.models import Confidence
from secondbrain.chat.context.optimization import ContextCandidate, SourceRanker
from secondbrain.rag.evidence_policy import EvidenceItem, EvidencePolicy

_WORD = re.compile(r"[\w-]+", re.UNICODE)
_NUMBER = re.compile(r"(?<!\w)\d+(?:[.,]\d+)?(?!\w)")
_SENTENCE = re.compile(r"(?<=[.!?])\s+|[\r\n]+")
_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in", "is", "it", "of", "on",
    "or", "that", "the", "this", "to", "was", "were", "will", "with", "what", "which", "who", "why",
    "der", "die", "das", "den", "dem", "ein", "eine", "einer", "eines", "ist", "sind", "und", "oder",
    "im", "in", "von", "zu", "mit", "was", "wie", "wer", "warum", "wird", "werden", "dass",
}


def _terms(text: str) -> set[str]:
    return {term.casefold() for term in _WORD.findall(text or "") if term.casefold() not in _STOPWORDS}


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _number(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _text(row: Mapping[str, Any]) -> str:
    return str(row.get("text") or row.get("snippet") or row.get("content") or row.get("preview") or "")


@dataclass(frozen=True)
class HallucinationFinding:
    claim: str
    support_score: float
    reason: str
    unsupported_numbers: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["support_score"] = round(self.support_score, 4)
        data["unsupported_numbers"] = list(self.unsupported_numbers)
        return data


@dataclass(frozen=True)
class HallucinationResult:
    score: float
    claim_count: int
    unsupported_claims: tuple[HallucinationFinding, ...]

    @property
    def detected(self) -> bool:
        return bool(self.unsupported_claims)

    @property
    def groundedness(self) -> float:
        return _clamp(1.0 - self.score) if self.claim_count else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "detected": self.detected,
            "score": round(self.score, 4),
            "groundedness": round(self.groundedness, 4),
            "claim_count": self.claim_count,
            "unsupported_claims": [item.to_dict() for item in self.unsupported_claims],
        }


@dataclass(frozen=True)
class SourceCheck:
    citation: dict[str, Any]
    verified: bool
    reason: str
    evidence_id: str = ""


@dataclass(frozen=True)
class SourceVerification:
    score: float
    checks: tuple[SourceCheck, ...]
    evidence_available: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": round(self.score, 4),
            "verified": sum(1 for row in self.checks if row.verified),
            "total": len(self.checks),
            "evidence_available": self.evidence_available,
            "checks": [asdict(row) for row in self.checks],
        }


@dataclass(frozen=True)
class EvidenceScore:
    evidence_id: str
    source: str
    relevance: float
    source_score: float
    completeness: float
    score: float


@dataclass(frozen=True)
class EvidenceRating:
    score: float
    items: tuple[EvidenceScore, ...]
    usable_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": round(self.score, 4),
            "rating": round(self.score * 100),
            "usable_count": self.usable_count,
            "items": [{**asdict(row), "relevance": round(row.relevance, 4),
                       "source_score": round(row.source_score, 4),
                       "completeness": round(row.completeness, 4), "score": round(row.score, 4)}
                      for row in self.items],
        }


@dataclass(frozen=True)
class AnswerRating:
    score: int
    stars: float
    groundedness: float
    source_verification: float
    evidence_quality: float
    clarity: float
    completeness: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SelfCritique:
    strengths: tuple[str, ...] = ()
    weaknesses: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {"strengths": list(self.strengths), "weaknesses": list(self.weaknesses)}


@dataclass(frozen=True)
class AnswerEvaluation:
    answer_rating: AnswerRating
    evidence_rating: EvidenceRating
    source_verification: SourceVerification
    hallucination: HallucinationResult
    confidence: Confidence
    self_critique: SelfCritique
    improvement_suggestions: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "answer_rating": self.answer_rating.to_dict(),
            "evidence_rating": self.evidence_rating.to_dict(),
            "source_verification": self.source_verification.to_dict(),
            "hallucination": self.hallucination.to_dict(),
            "confidence": self.confidence.to_dict(),
            "self_critique": self.self_critique.to_dict(),
            "improvement_suggestions": list(self.improvement_suggestions),
        }


class HallucinationDetector:
    def __init__(self, *, support_threshold: float = 0.75) -> None:
        self.support_threshold = _clamp(support_threshold)

    def detect(self, answer: str, evidence: Iterable[Mapping[str, Any]]) -> HallucinationResult:
        evidence_texts = [_text(row) for row in evidence if _text(row).strip()]
        evidence_terms = [_terms(text) for text in evidence_texts]
        evidence_numbers = set(_NUMBER.findall(" ".join(evidence_texts)))
        claims = []
        for part in _SENTENCE.split(answer or ""):
            claim = re.sub(r"\[\d+\]", "", part).strip(" -\t")
            if _terms(claim):
                claims.append(claim)
        findings: list[HallucinationFinding] = []
        for claim in claims:
            terms = _terms(claim)
            support = max((len(terms & source_terms) / len(terms) for source_terms in evidence_terms), default=0.0)
            unsupported_numbers = tuple(sorted(set(_NUMBER.findall(claim)) - evidence_numbers))
            if unsupported_numbers:
                findings.append(HallucinationFinding(claim, support, "unsupported_numeric_claim", unsupported_numbers))
            elif support < self.support_threshold:
                findings.append(HallucinationFinding(claim, support, "insufficient_evidence_overlap"))
        score = len(findings) / len(claims) if claims else 0.0
        return HallucinationResult(_clamp(score), len(claims), tuple(findings))


class SourceVerifier:
    def verify(self, citations: Iterable[Mapping[str, Any]], evidence: Iterable[Mapping[str, Any]]) -> SourceVerification:
        evidence_rows = list(evidence)
        checks: list[SourceCheck] = []
        for citation in citations:
            citation_row = dict(citation)
            match = next((row for row in evidence_rows if self._matches(citation_row, row)), None)
            verified = bool(match is not None and _text(match).strip())
            checks.append(SourceCheck(
                citation=citation_row,
                verified=verified,
                reason="matched_retrieval_evidence" if verified else "source_not_found",
                evidence_id=self._identifier(match or {}),
            ))
        score = sum(1 for row in checks if row.verified) / len(checks) if checks else 0.0
        return SourceVerification(score, tuple(checks), bool(evidence_rows))

    @staticmethod
    def _matches(citation: Mapping[str, Any], evidence: Mapping[str, Any]) -> bool:
        if citation.get("chunk") not in (None, ""):
            return str(citation["chunk"]) == str(evidence.get("chunk_id"))
        if citation.get("document_id") not in (None, ""):
            return str(citation["document_id"]) == str(evidence.get("document_id"))
        return citation.get("source") not in (None, "") and str(citation["source"]) == str(evidence.get("source"))

    @staticmethod
    def _identifier(row: Mapping[str, Any]) -> str:
        return str(row.get("chunk_id") or row.get("document_id") or row.get("memory_id") or row.get("id") or "")


class EvidenceRater:
    def __init__(self, policy: EvidencePolicy | None = None, source_ranker: SourceRanker | None = None) -> None:
        self.policy = policy or EvidencePolicy()
        self.source_ranker = source_ranker or SourceRanker()

    def rate(self, question: str, answer: str, evidence: Iterable[Mapping[str, Any]]) -> EvidenceRating:
        rows = list(evidence)
        answer_terms, question_terms = _terms(answer), _terms(question)
        scores: list[EvidenceScore] = []
        policy_items: list[EvidenceItem] = []
        for index, row in enumerate(rows):
            text = _text(row)
            identifier = SourceVerifier._identifier(row) or f"evidence-{index}"
            source = str(row.get("source") or row.get("provider") or "")
            raw_score = _clamp(_number(row.get("hybrid_score", row.get("score", row.get("confidence", 0.5))), 0.5))
            policy_items.append(EvidenceItem(identifier, str(row.get("title") or identifier), text, raw_score))
            terms = _terms(text)
            answer_relevance = len(terms & answer_terms) / len(answer_terms) if answer_terms else 0.0
            question_relevance = len(terms & question_terms) / len(question_terms) if question_terms else 0.0
            relevance = _clamp(0.65 * answer_relevance + 0.35 * question_relevance)
            section = "semantic_memory" if row.get("memory_id") else "documents"
            source_score = self.source_ranker.score(ContextCandidate(
                identifier, text, section, source, raw_score, metadata=dict(row)
            ))
            completeness = (float(bool(identifier)) + float(bool(source)) + float(bool(text.strip()))) / 3.0
            score = _clamp(0.4 * relevance + 0.25 * source_score + 0.2 * raw_score + 0.15 * completeness)
            scores.append(EvidenceScore(identifier, source, relevance, source_score, completeness, score))
        usable = self.policy.evaluate(policy_items).usable_items
        overall = sum(row.score for row in scores) / len(scores) if scores else 0.0
        return EvidenceRating(_clamp(overall), tuple(sorted(scores, key=lambda row: (-row.score, row.evidence_id))), len(usable))


class AnswerRater:
    def rate(self, question: str, answer: str, hallucination: HallucinationResult,
             sources: SourceVerification, evidence: EvidenceRating) -> AnswerRating:
        answer_terms, question_terms = _terms(answer), _terms(question)
        clarity = 0.0 if not answer.strip() else 1.0 if 10 <= len(answer.strip()) <= 8000 else 0.7
        completeness = len(answer_terms & question_terms) / len(question_terms) if question_terms else float(bool(answer_terms))
        factors = (
            hallucination.groundedness,
            sources.score,
            evidence.score,
            clarity,
            _clamp(completeness),
        )
        score = round(100 * (0.35 * factors[0] + 0.2 * factors[1] + 0.2 * factors[2] + 0.15 * factors[3] + 0.1 * factors[4]))
        return AnswerRating(score, round(score / 20, 1), *[round(value, 4) for value in factors])


class SelfCritic:
    def critique(self, rating: AnswerRating, hallucination: HallucinationResult,
                 sources: SourceVerification, evidence: EvidenceRating) -> SelfCritique:
        strengths: list[str] = []
        weaknesses: list[str] = []
        if hallucination.groundedness >= 0.8:
            strengths.append("Most substantive claims are supported by retrieved evidence.")
        if sources.score == 1.0 and sources.checks:
            strengths.append("All cited sources resolve to retrieved evidence.")
        if rating.clarity >= 0.9:
            strengths.append("The answer is concise and structurally clear.")
        if hallucination.detected:
            weaknesses.append("One or more claims are not sufficiently supported by the supplied evidence.")
        if sources.score < 1.0:
            weaknesses.append("Source coverage or source verification is incomplete.")
        if evidence.usable_count == 0:
            weaknesses.append("No usable evidence satisfies the grounding policy.")
        if rating.completeness < 0.5:
            weaknesses.append("The answer does not cover enough of the user question.")
        return SelfCritique(tuple(strengths), tuple(weaknesses))


class ImprovementSuggester:
    def suggest(self, critique: SelfCritique, hallucination: HallucinationResult,
                sources: SourceVerification, evidence: EvidenceRating) -> tuple[str, ...]:
        suggestions: list[str] = []
        if hallucination.detected:
            suggestions.append("Remove, qualify, or retrieve evidence for unsupported claims.")
        if sources.score < 1.0:
            suggestions.append("Add valid citations for factual claims and remove unresolved source references.")
        if evidence.usable_count == 0:
            suggestions.append("Retrieve stronger evidence before presenting a definitive answer.")
        if any("user question" in item for item in critique.weaknesses):
            suggestions.append("Address the missing terms and intent from the user question explicitly.")
        return tuple(dict.fromkeys(suggestions))


class AnswerEvaluator:
    def __init__(self, *, hallucinations: HallucinationDetector | None = None,
                 sources: SourceVerifier | None = None, evidence: EvidenceRater | None = None,
                 answers: AnswerRater | None = None, critic: SelfCritic | None = None,
                 improvements: ImprovementSuggester | None = None) -> None:
        self.hallucinations = hallucinations or HallucinationDetector()
        self.sources = sources or SourceVerifier()
        self.evidence = evidence or EvidenceRater()
        self.answers = answers or AnswerRater()
        self.critic = critic or SelfCritic()
        self.improvements = improvements or ImprovementSuggester()

    def evaluate(self, question: str, answer: str, *, evidence: Iterable[Mapping[str, Any]] = (),
                 citations: Iterable[Mapping[str, Any]] = ()) -> AnswerEvaluation:
        evidence_rows = list(evidence)
        hallucination = self.hallucinations.detect(answer, evidence_rows)
        source_verification = self.sources.verify(citations, evidence_rows)
        evidence_rating = self.evidence.rate(question, answer, evidence_rows)
        answer_rating = self.answers.rate(question, answer, hallucination, source_verification, evidence_rating)
        factors = {
            "groundedness": hallucination.groundedness,
            "source_verification": source_verification.score,
            "evidence_quality": evidence_rating.score,
            "answer_quality": answer_rating.score / 100,
        }
        confidence = Confidence(score=_clamp(
            0.4 * factors["groundedness"] + 0.25 * factors["source_verification"]
            + 0.2 * factors["evidence_quality"] + 0.15 * factors["answer_quality"]
        ), factors=factors)
        critique = self.critic.critique(answer_rating, hallucination, source_verification, evidence_rating)
        suggestions = self.improvements.suggest(critique, hallucination, source_verification, evidence_rating)
        return AnswerEvaluation(answer_rating, evidence_rating, source_verification, hallucination,
                                confidence, critique, suggestions)
