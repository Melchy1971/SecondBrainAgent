"""Gemini embedding provider adapter.

The implementation uses an injectable client to keep tests deterministic and to
avoid a hard dependency on a specific Google SDK. A real client only needs an
``embed(texts, model=...)`` method returning ``list[list[float]]``.
"""

from __future__ import annotations

import os
from typing import Protocol

from secondbrain.rag.providers.base import EmbeddingProviderConfig, EmbeddingProviderError, normalize_vectors


class GeminiEmbeddingClient(Protocol):
    def embed(self, texts: list[str], model: str) -> list[list[float]]:
        ...


class GeminiEmbeddingProvider:
    name = "gemini"

    def __init__(
        self,
        model: str = "text-embedding-004",
        api_key: str | None = None,
        client: GeminiEmbeddingClient | None = None,
    ) -> None:
        self.model = model
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.client = client

    @classmethod
    def from_config(cls, config: EmbeddingProviderConfig) -> "GeminiEmbeddingProvider":
        return cls(model=config.model or "text-embedding-004", api_key=config.api_key, client=config.extra.get("client"))

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if self.client is None:
            raise EmbeddingProviderError(
                "Gemini embedding client is not configured. Inject a client or configure the SDK adapter."
            )
        if not self.api_key:
            raise EmbeddingProviderError("GEMINI_API_KEY or GOOGLE_API_KEY is required for Gemini embeddings")
        return normalize_vectors(self.client.embed(texts, model=self.model), expected_count=len(texts))
