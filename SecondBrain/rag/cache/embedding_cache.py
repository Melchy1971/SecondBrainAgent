"""Provider-aware embedding cache service.

Cache identity includes provider, model, normalized text, and an optional schema
version. This prevents vector reuse across incompatible providers/models while
keeping deterministic keys for incremental indexing.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

from secondbrain.rag.providers.base import EmbeddingProvider, EmbeddingProviderError


def normalize_cache_text(text: str) -> str:
    """Normalize whitespace without lowercasing or removing punctuation."""

    return " ".join((text or "").strip().split())


def build_embedding_cache_key(
    text: str,
    *,
    provider: str,
    model: str | None,
    schema_version: str = "v1",
) -> str:
    """Build stable SHA-256 key for one embedding request."""

    payload = "\u241f".join(
        [schema_version, provider.strip().lower(), (model or "").strip(), normalize_cache_text(text)]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class CachedEmbedding:
    """Cached vector plus provenance metadata."""

    text_hash: str
    provider: str
    model: str | None
    vector: list[float]
    created_at: datetime
    dimensions: int
    schema_version: str = "v1"


@dataclass(frozen=True)
class CacheStats:
    """Runtime counters for one cache service instance."""

    hits: int
    misses: int
    writes: int
    entries: int

    @property
    def requests(self) -> int:
        return self.hits + self.misses

    @property
    def hit_rate(self) -> float:
        return 0.0 if self.requests == 0 else self.hits / self.requests


class EmbeddingCacheService:
    """Read-through cache wrapper around an embedding provider."""

    def __init__(self, repository, *, schema_version: str = "v1") -> None:
        self.repository = repository
        self.schema_version = schema_version
        self._hits = 0
        self._misses = 0
        self._writes = 0

    def key_for(self, text: str, provider: EmbeddingProvider) -> str:
        return build_embedding_cache_key(
            text,
            provider=provider.name,
            model=provider.model,
            schema_version=self.schema_version,
        )

    def get(self, text: str, provider: EmbeddingProvider) -> list[float] | None:
        key = self.key_for(text, provider)
        item = self.repository.get(key)
        if item is None:
            self._misses += 1
            return None
        self._hits += 1
        return list(item.vector)

    def put(self, text: str, vector: Iterable[float], provider: EmbeddingProvider) -> str:
        values = [float(value) for value in vector]
        if not values:
            raise EmbeddingProviderError("cannot cache empty embedding vector")
        key = self.key_for(text, provider)
        self.repository.put(
            CachedEmbedding(
                text_hash=key,
                provider=provider.name,
                model=provider.model,
                vector=values,
                created_at=datetime.now(timezone.utc),
                dimensions=len(values),
                schema_version=self.schema_version,
            )
        )
        self._writes += 1
        return key

    def embed_texts(self, texts: list[str], provider: EmbeddingProvider) -> list[list[float]]:
        """Return embeddings while only asking provider for cache misses."""

        if not texts:
            return []

        result: list[list[float] | None] = [None] * len(texts)
        missing_positions: list[int] = []
        missing_texts: list[str] = []

        for index, text in enumerate(texts):
            cached = self.get(text, provider)
            if cached is None:
                missing_positions.append(index)
                missing_texts.append(text)
            else:
                result[index] = cached

        if missing_texts:
            vectors = provider.embed(missing_texts)
            if len(vectors) != len(missing_texts):
                raise EmbeddingProviderError(
                    f"provider returned {len(vectors)} vectors for {len(missing_texts)} cache misses"
                )
            for index, vector in zip(missing_positions, vectors, strict=True):
                self.put(texts[index], vector, provider)
                result[index] = [float(value) for value in vector]

        return [vector for vector in result if vector is not None]

    def invalidate(self, text: str, provider: EmbeddingProvider) -> bool:
        return self.repository.delete(self.key_for(text, provider))

    def stats(self) -> CacheStats:
        return CacheStats(
            hits=self._hits,
            misses=self._misses,
            writes=self._writes,
            entries=self.repository.count(),
        )
