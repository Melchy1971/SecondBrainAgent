"""Embedding cache keyed by provider:model:dimensions:content-hash."""

from __future__ import annotations

from secondbrain.embeddings.base import EmbeddingProvider, ProviderHealth, content_key


class EmbeddingCache:
    def __init__(self) -> None:
        self._store: dict[str, list[float]] = {}
        self.hits = 0
        self.misses = 0

    def get(self, key: str):
        v = self._store.get(key)
        if v is None:
            self.misses += 1
        else:
            self.hits += 1
        return v

    def put(self, key: str, vector: list[float]) -> None:
        self._store[key] = vector

    def stats(self) -> dict:
        return {"size": len(self._store), "hits": self.hits, "misses": self.misses}


class CachingEmbeddingProvider:
    """Wraps a provider with a content-addressed cache. Delegates health/identity."""

    def __init__(self, provider: EmbeddingProvider, cache: EmbeddingCache | None = None) -> None:
        self.provider = provider
        self.cache = cache or EmbeddingCache()
        self.name = provider.name
        self.model = provider.model
        self.dimensions = provider.dimensions
        self.semantic = getattr(provider, "semantic", False)

    def _key(self, text: str) -> str:
        return content_key(self.name, self.model, self.dimensions, text)

    def embed(self, text: str) -> list[float]:
        key = self._key(text)
        cached = self.cache.get(key)
        if cached is not None:
            return cached
        vec = self.provider.embed(text)
        self.cache.put(key, vec)
        return vec

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        result: list[list[float] | None] = [None] * len(texts)
        missing_idx, missing_txt = [], []
        for i, t in enumerate(texts):
            cached = self.cache.get(self._key(t))
            if cached is not None:
                result[i] = cached
            else:
                missing_idx.append(i)
                missing_txt.append(t)
        if missing_txt:
            fetched = self.provider.embed_batch(missing_txt)
            for i, t, v in zip(missing_idx, missing_txt, fetched):
                self.cache.put(self._key(t), v)
                result[i] = v
        return [r for r in result]  # type: ignore[return-value]

    def health(self) -> ProviderHealth:
        return self.provider.health()
