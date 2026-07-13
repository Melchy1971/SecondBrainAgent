"""Deterministic local embedding provider. DEV_ONLY - never production.

Stable hash-based projection with no network dependency. It is NOT semantic and
is NOT a fallback: production code must never substitute it for a real provider.
It exists only for development and tests. ``production_ready`` is always ``False``
so the production gate blocks it regardless of a passing structural probe.
"""

from __future__ import annotations

import hashlib
import math

from secondbrain.rag.providers.base import (
    EmbeddingBatch,
    EmbeddingProviderConfig,
    EmbeddingResult,
    ProviderHealthReport,
)


class DeterministicEmbeddingProvider:
    """Deterministic hash-based embeddings for development and tests only.

    DEV_ONLY: not semantic, not production-ready, never used as a silent
    fallback for an unavailable real provider.
    """

    name = "deterministic"
    semantic = False
    production_ready = False
    dev_only = True

    def __init__(self, dimensions: int = 64, model: str = "hash-v1") -> None:
        if dimensions <= 0:
            raise ValueError("dimensions must be greater than zero")
        self.dimensions = dimensions
        self.model = model

    @classmethod
    def from_config(cls, config: EmbeddingProviderConfig) -> "DeterministicEmbeddingProvider":
        return cls(dimensions=config.dimensions or 64, model=config.model or "hash-v1")

    def health(self) -> ProviderHealthReport:
        """Structural probe passes, but the provider is never production-ready."""
        return ProviderHealthReport(
            status="PASS",
            provider=self.name,
            model=self.model,
            dimensions=self.dimensions,
            semantic=False,
            production_ready=False,
            dev_only=True,
            error="deterministic embeddings are DEV_ONLY and never production-ready",
        )

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
