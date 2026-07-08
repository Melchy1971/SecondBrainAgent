"""P3 v20.0 - Semantic Memory Foundation."""

from __future__ import annotations
from dataclasses import dataclass
from time import time


@dataclass
class SemanticMemoryItem:
    memory_id: str
    text: str
    score: float = 0.0
    created_at: float = time()


class SemanticMemoryStore:
    def __init__(self):
        self._items: dict[str, SemanticMemoryItem] = {}

    def upsert(self, item: SemanticMemoryItem) -> None:
        self._items[item.memory_id] = item

    def get(self, memory_id: str) -> SemanticMemoryItem | None:
        return self._items.get(memory_id)

    def list(self) -> list[SemanticMemoryItem]:
        return list(self._items.values())
