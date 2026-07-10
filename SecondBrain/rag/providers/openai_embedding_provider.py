"""OpenAI-compatible embedding provider.

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
from secondbrain.rag.providers.openai_http_client import OpenAIEmbeddingError, OpenAIHttpClient

_PROBE_TEXT = "secondbrain health probe"


class OpenAIEmbeddingProvider(EmbeddingProvider):
    name = "openai"
    semantic = True
    production_ready = True
    dev_only = False

    def __init__(
        self,
        model: str = "text-embedding-3-small",
        client: OpenAIHttpClient | None = None,
        *,
        dimensions: int | None = None,
        enforce_dimensions: bool = False,
    ) -> None:
        self.model = model
        self.client = client or OpenAIHttpClient()
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
        except (DimensionMismatchError, OpenAIEmbeddingError) as exc:
            return ProviderHealthReport("FAIL", self.name, self.model, self.dimensions, True, False, False, str(exc))
        except Exception as exc:  # noqa: BLE001 - health boundary, report FAIL not fake
            return ProviderHealthReport("FAIL", self.name, self.model, self.dimensions, True, False, False, str(exc))
        return ProviderHealthReport("PASS", self.name, self.model, len(vector), True, True, False, None)
