"""P1 v19.5 - evidence policy for RAG answers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EvidenceItem:
    source_id: str
    title: str
    excerpt: str
    score: float


@dataclass(frozen=True)
class EvidenceDecision:
    status: str
    reason: str
    usable_items: list[EvidenceItem]


class EvidencePolicy:
    def __init__(self, min_items: int = 1, min_score: float = 0.01) -> None:
        self.min_items = min_items
        self.min_score = min_score

    def evaluate(self, items: list[EvidenceItem]) -> EvidenceDecision:
        usable = [
            item for item in items
            if item.source_id and item.excerpt.strip() and float(item.score) >= self.min_score
        ]
        if len(usable) < self.min_items:
            return EvidenceDecision(
                status="NO_EVIDENCE",
                reason="Insufficient usable evidence for grounded answer.",
                usable_items=usable,
            )
        return EvidenceDecision(status="PASS", reason="Evidence available.", usable_items=usable)
