"""Repository contracts and in-memory implementation for embedding cache entries."""

from __future__ import annotations

from copy import deepcopy
from typing import Protocol

from secondbrain.rag.cache.embedding_cache import CachedEmbedding


class EmbeddingCacheRepository(Protocol):
    """Persistence contract for cached embedding vectors."""

    def get(self, key: str) -> CachedEmbedding | None:
        """Return cached item by deterministic key."""

    def put(self, item: CachedEmbedding) -> None:
        """Persist or replace a cached item."""

    def delete(self, key: str) -> bool:
        """Delete an item. Return whether an item existed."""

    def count(self) -> int:
        """Return number of cached entries."""

    def clear(self) -> None:
        """Remove all cached entries."""


class InMemoryEmbeddingCacheRepository:
    """Process-local repository for tests and desktop/offline mode.

    The repository stores defensive copies. Callers cannot mutate cached vectors
    through returned objects and accidentally corrupt later reads.
    """

    def __init__(self) -> None:
        self._items: dict[str, CachedEmbedding] = {}

    def get(self, key: str) -> CachedEmbedding | None:
        item = self._items.get(key)
        return deepcopy(item) if item is not None else None

    def put(self, item: CachedEmbedding) -> None:
        self._items[item.text_hash] = deepcopy(item)

    def delete(self, key: str) -> bool:
        existed = key in self._items
        self._items.pop(key, None)
        return existed

    def count(self) -> int:
        return len(self._items)

    def clear(self) -> None:
        self._items.clear()
