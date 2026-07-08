"""P1 v19.3 - batch embedding pipeline with cache support."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from secondbrain.rag.embedding_cache import EmbeddingCache


class EmbeddingProviderProtocol(Protocol):
    provider_name: str
    model: str

    def embed(self, texts: list[str]) -> list[list[float]]:
        ...


@dataclass(frozen=True)
class BatchEmbeddingResult:
    texts: int
    generated: int
    cache_hits: int
    vectors: list[list[float]]


class BatchEmbeddingPipeline:
    def __init__(self, provider: EmbeddingProviderProtocol, cache: EmbeddingCache | None = None, batch_size: int = 32) -> None:
        if batch_size < 1:
            raise ValueError("batch_size must be >= 1")
        self.provider = provider
        self.cache = cache or EmbeddingCache()
        self.batch_size = batch_size

    def run(self, texts: list[str]) -> BatchEmbeddingResult:
        vectors: list[list[float] | None] = [None] * len(texts)
        missing_indices: list[int] = []
        cache_hits = 0

        for idx, text in enumerate(texts):
            cached = self.cache.get(text, provider=self.provider.provider_name, model=self.provider.model)
            if cached is None:
                missing_indices.append(idx)
            else:
                vectors[idx] = cached
                cache_hits += 1

        generated = 0
        for start in range(0, len(missing_indices), self.batch_size):
            batch_indices = missing_indices[start:start + self.batch_size]
            batch_texts = [texts[i] for i in batch_indices]
            batch_vectors = self.provider.embed(batch_texts)
            if len(batch_vectors) != len(batch_texts):
                raise ValueError("provider returned a different number of vectors than requested")
            for idx, vector in zip(batch_indices, batch_vectors):
                vector = [float(x) for x in vector]
                vectors[idx] = vector
                self.cache.put(texts[idx], vector, provider=self.provider.provider_name, model=self.provider.model)
                generated += 1

        return BatchEmbeddingResult(
            texts=len(texts),
            generated=generated,
            cache_hits=cache_hits,
            vectors=[v or [] for v in vectors],
        )
