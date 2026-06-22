"""P1 v19.5 - grounded answer composer.

This module intentionally avoids LLM generation. It composes an extractive,
citation-backed answer from retrieved evidence. Later P2 agent runtime may
replace the surface wording, but the evidence contract stays.
"""

from __future__ import annotations

from dataclasses import dataclass

from secondbrain.rag.evidence_policy import EvidenceItem, EvidencePolicy


@dataclass(frozen=True)
class GroundedAnswer:
    status: str
    answer: str
    citations: list[str]
    evidence_count: int


class AnswerComposer:
    def __init__(self, policy: EvidencePolicy | None = None) -> None:
        self.policy = policy or EvidencePolicy()

    def compose(self, query: str, evidence: list[EvidenceItem], *, max_items: int = 3) -> GroundedAnswer:
        decision = self.policy.evaluate(evidence)
        if decision.status != "PASS":
            return GroundedAnswer(
                status="NO_EVIDENCE",
                answer="Keine belastbare Antwort möglich: Es wurden keine ausreichenden Quellen gefunden.",
                citations=[],
                evidence_count=len(decision.usable_items),
            )

        selected = decision.usable_items[:max_items]
        parts = []
        citations = []
        for idx, item in enumerate(selected, start=1):
            clean_excerpt = " ".join(item.excerpt.strip().split())
            parts.append(f"{idx}. {clean_excerpt}")
            citations.append(item.source_id)

        return GroundedAnswer(
            status="PASS",
            answer="\n".join(parts),
            citations=citations,
            evidence_count=len(selected),
        )
