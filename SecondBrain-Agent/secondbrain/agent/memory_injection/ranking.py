"""v30.64 Agent Memory Injection - MemoryRanking.

Scores each candidate memory by relevance to the query and recency, and derives
a confidence in [0, 1]. Deterministic and dependency-free so previews are
reproducible and auditable.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

_WORD = re.compile(r"[A-Za-zÀ-ÿ0-9]+")


def _terms(text: str) -> list[str]:
    return [t.lower() for t in _WORD.findall(text or "")]


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


@dataclass(frozen=True)
class RankedMemory:
    record: Any
    relevance: float
    recency_days: int
    recency_factor: float
    confidence: float
    score: float


class MemoryRanking:
    def __init__(self, *, recency_halflife_days: float = 30.0,
                 relevance_weight: float = 0.65, recency_weight: float = 0.35):
        self.recency_halflife_days = recency_halflife_days
        self.relevance_weight = relevance_weight
        self.recency_weight = recency_weight

    def relevance(self, record, query_text: str) -> float:
        q = _terms(query_text)
        if not q:
            return 1.0  # no query -> everything is equally (fully) relevant
        text_lower = (getattr(record, "text", "") or "").lower()
        text_terms = set(_terms(text_lower))
        matched = sum(1 for term in q if term in text_terms)
        base = matched / len(q)
        # exact phrase boost
        if query_text.strip().lower() in text_lower:
            base = max(base, 0.9)
        return _clamp(base)

    def recency(self, record, now: datetime) -> tuple[int, float]:
        created = getattr(record, "created_at", None)
        if not isinstance(created, datetime):
            return 0, 1.0
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        age_days = max(0, (now - created).days)
        factor = 1.0 / (1.0 + age_days / max(1e-9, self.recency_halflife_days))
        return age_days, _clamp(factor)

    def confidence(self, relevance: float, recency_factor: float, record) -> float:
        metadata = getattr(record, "metadata", {}) or {}
        computed = 0.6 * relevance + 0.4 * recency_factor
        meta_conf = metadata.get("confidence")
        if isinstance(meta_conf, (int, float)):
            return _clamp(0.5 * float(meta_conf) + 0.5 * computed)
        return _clamp(computed)

    def rank(self, records, query_text: str, *, now: datetime | None = None) -> list[RankedMemory]:
        current = now or datetime.now(timezone.utc)
        ranked: list[RankedMemory] = []
        for record in records:
            rel = self.relevance(record, query_text)
            age_days, rec_factor = self.recency(record, current)
            conf = self.confidence(rel, rec_factor, record)
            score = self.relevance_weight * rel + self.recency_weight * rec_factor
            ranked.append(RankedMemory(record, rel, age_days, rec_factor, conf, score))
        ranked.sort(key=lambda r: (r.score, -r.recency_days), reverse=True)
        return ranked
