"""Ollama embedding provider."""

from __future__ import annotations

from secondbrain.rag.embedding_provider import EmbeddingProvider
from secondbrain.rag.providers.ollama_http_client import OllamaHttpClient


class OllamaEmbeddingProvider(EmbeddingProvider):
    def __init__(
        self,
        host: str = "http://localhost:11434",
        model: str = "nomic-embed-text",
        client: OllamaHttpClient | None = None,
    ) -> None:
        self.host = host
        self.model = model
        self.client = client or OllamaHttpClient(host=host)

    def embed(self, texts: list[str]) -> list[list[float]]:
        return self.client.embed(texts, model=self.model)
