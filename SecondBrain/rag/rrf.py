"""P1 v19.4 - Reciprocal Rank Fusion.

Combines multiple ranked result lists without requiring comparable raw scores.
Formula: score += 1 / (k + rank)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


@dataclass(frozen=True)
class RankedItem:
    id: str
    score: float = 0.0
    payload: dict = field(default_factory=dict)


@dataclass(frozen=True)
class FusedItem:
    id: str
    score: float
    sources: list[str]
    payload: dict


def reciprocal_rank_fusion(
    rankings: dict[str, list[RankedItem]],
    *,
    k: int = 60,
    limit: int | None = None,
) -> list[FusedItem]:
    if k < 1:
        raise ValueError("k must be >= 1")

    scores: dict[str, float] = {}
    sources: dict[str, list[str]] = {}
    payloads: dict[str, dict] = {}

    for source_name, items in rankings.items():
        for rank, item in enumerate(items, start=1):
            scores[item.id] = scores.get(item.id, 0.0) + (1.0 / (k + rank))
            sources.setdefault(item.id, []).append(source_name)
            payloads.setdefault(item.id, item.payload)

    fused = [
        FusedItem(id=item_id, score=score, sources=sources[item_id], payload=payloads[item_id])
        for item_id, score in scores.items()
    ]
    fused.sort(key=lambda item: (-item.score, item.id))
    return fused if limit is None else fused[:limit]
