"""v30.2 - vector storage models."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class VectorRecord:
    id: str
    owner_type: str
    owner_id: str
    provider: str
    model: str
    embedding: list[float]
    metadata: dict = field(default_factory=dict)

    @property
    def dimension(self) -> int:
        return len(self.embedding)


@dataclass(frozen=True)
class VectorSearchResult:
    id: str
    owner_type: str
    owner_id: str
    distance: float
    score: float
    metadata: dict
