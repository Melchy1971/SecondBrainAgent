"""P0.2 - deterministic hybrid scoring for vector retrieval.

Combines semantic, lexical, recency and importance signals into one bounded score.
The implementation is dependency-free so it is safe for local tests and CLI usage.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Mapping


@dataclass(frozen=True)
class HybridScoreWeights:
    semantic: float = 0.55
    bm25: float = 0.25
    recency: float = 0.10
    importance: float = 0.10

    def normalized(self) -> "HybridScoreWeights":
        values = {
            "semantic": _valid_weight(self.semantic),
            "bm25": _valid_weight(self.bm25),
            "recency": _valid_weight(self.recency),
            "importance": _valid_weight(self.importance),
        }
        total = sum(values.values())
        if total <= 0:
            raise ValueError("At least one hybrid score weight must be greater than zero")
        return HybridScoreWeights(**{key: value / total for key, value in values.items()})


def _valid_weight(value: float) -> float:
    value = float(value)
    if not isfinite(value) or value < 0:
        raise ValueError("Hybrid score weights must be finite non-negative numbers")
    return value


def _clamp01(value: float | int | None) -> float:
    if value is None:
        return 0.0
    value = float(value)
    if not isfinite(value):
        return 0.0
    return max(0.0, min(1.0, value))


class HybridScoreCalculator:
    def __init__(self, weights: HybridScoreWeights | None = None) -> None:
        self.weights = (weights or HybridScoreWeights()).normalized()

    def score(
        self,
        *,
        semantic_score: float,
        bm25_score: float = 0.0,
        recency_score: float = 0.0,
        importance_score: float = 0.0,
    ) -> float:
        weighted = (
            _clamp01(semantic_score) * self.weights.semantic
            + _clamp01(bm25_score) * self.weights.bm25
            + _clamp01(recency_score) * self.weights.recency
            + _clamp01(importance_score) * self.weights.importance
        )
        return round(weighted, 6)

    def score_mapping(self, scores: Mapping[str, float | int | None]) -> float:
        return self.score(
            semantic_score=scores.get("semantic_score", scores.get("semantic", 0.0)),
            bm25_score=scores.get("bm25_score", scores.get("bm25", 0.0)),
            recency_score=scores.get("recency_score", scores.get("recency", 0.0)),
            importance_score=scores.get("importance_score", scores.get("importance", 0.0)),
        )
