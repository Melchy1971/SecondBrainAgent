"""OpenAI-compatible embedding provider."""

from __future__ import annotations

from secondbrain.rag.embedding_provider import EmbeddingProvider
from secondbrain.rag.providers.openai_http_client import OpenAIHttpClient


class OpenAIEmbeddingProvider(EmbeddingProvider):
    def __init__(
        self,
        model: str = "text-embedding-3-small",
        client: OpenAIHttpClient | None = None,
    ) -> None:
        self.model = model
        self.client = client or OpenAIHttpClient()

    def embed(self, texts: list[str]) -> list[list[float]]:
        return self.client.embed(texts, model=self.model)
