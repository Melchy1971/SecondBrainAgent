"""Deterministic local embedding provider used for tests and offline fallback."""

from __future__ import annotations

import hashlib
import math

from secondbrain.rag.providers.base import EmbeddingBatch, EmbeddingProviderConfig, EmbeddingResult


class DeterministicEmbeddingProvider:
    """Stable hash-based embeddings with no network dependency.

    This is not semantic quality. It is a safe offline fallback for development,
    tests, and degraded operation when real embedding services are unavailable.
    """

    name = "deterministic"

    def __init__(self, dimensions: int = 64, model: str = "hash-v1") -> None:
        if dimensions <= 0:
            raise ValueError("dimensions must be greater than zero")
        self.dimensions = dimensions
        self.model = model

    @classmethod
    def from_config(cls, config: EmbeddingProviderConfig) -> "DeterministicEmbeddingProvider":
        return cls(dimensions=config.dimensions or 64, model=config.model or "hash-v1")

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            seed = hashlib.sha256(text.encode("utf-8")).digest()
            values: list[float] = []
            counter = 0
            while len(values) < self.dimensions:
                block = hashlib.sha256(seed + counter.to_bytes(4, "big")).digest()
                for byte in block:
                    values.append((byte / 127.5) - 1.0)
                    if len(values) == self.dimensions:
                        break
                counter += 1
            norm = math.sqrt(sum(value * value for value in values)) or 1.0
            vectors.append([value / norm for value in values])
        return vectors

    def embed_batch(self, batch: EmbeddingBatch) -> EmbeddingResult:
        vectors = self.embed(batch.texts)
        return EmbeddingResult(vectors=vectors, provider=self.name, model=batch.model or self.model, dimensions=self.dimensions)
