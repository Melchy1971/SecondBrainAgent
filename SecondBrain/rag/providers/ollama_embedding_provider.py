"""Ollama embedding provider.

Networked, semantic, production-capable. On any failure it raises (via the HTTP
client) - it never returns a fake or fallback vector. ``health()`` runs a live
probe and returns FAIL on error instead of masking the outage.
"""

from __future__ import annotations

from secondbrain.rag.embedding_provider import EmbeddingProvider
from secondbrain.rag.providers.base import (
    DimensionMismatchError,
    ProviderHealthReport,
    validate_dimensions,
)
from secondbrain.rag.providers.ollama_http_client import OllamaEmbeddingError, OllamaHttpClient

_PROBE_TEXT = "secondbrain health probe"


class OllamaEmbeddingProvider(EmbeddingProvider):
    name = "ollama"
    semantic = True
    production_ready = True
    dev_only = False

    def __init__(
        self,
        host: str = "http://localhost:11434",
        model: str = "nomic-embed-text",
        client: OllamaHttpClient | None = None,
        *,
        dimensions: int | None = None,
        enforce_dimensions: bool = False,
    ) -> None:
        self.host = host
        self.model = model
        self.client = client or OllamaHttpClient(host=host)
        self.dimensions = int(dimensions) if dimensions else 0
        self.enforce_dimensions = bool(enforce_dimensions)

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = self.client.embed(texts, model=self.model)
        if self.enforce_dimensions and self.dimensions and vectors:
            validate_dimensions(vectors, self.dimensions)
        return vectors

    def health(self) -> ProviderHealthReport:
        try:
            vector = self.embed([_PROBE_TEXT])[0]
        except (DimensionMismatchError, OllamaEmbeddingError) as exc:
            return ProviderHealthReport("FAIL", self.name, self.model, self.dimensions, True, False, False, str(exc))
        except Exception as exc:  # noqa: BLE001 - health boundary, report FAIL not fake
            return ProviderHealthReport("FAIL", self.name, self.model, self.dimensions, True, False, False, str(exc))
        return ProviderHealthReport("PASS", self.name, self.model, len(vector), True, True, False, None)
