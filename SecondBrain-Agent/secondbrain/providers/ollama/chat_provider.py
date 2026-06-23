"""v30.0 Ollama local provider."""
from __future__ import annotations

from typing import Iterable

from secondbrain.providers.base.http_transport import JsonHttpTransport
from secondbrain.providers.base.provider_capabilities import ProviderCapabilities
from secondbrain.providers.base.provider_exception import ProviderError
from secondbrain.providers.base.provider_models import CompletionRequest, CompletionResponse, EmbeddingRequest, EmbeddingResponse, StreamChunk, messages_to_openai


class OllamaProvider:
    name = "ollama"
    capabilities = ProviderCapabilities(chat=True, embeddings=True, streaming=False, local=True)

    def __init__(self, base_url: str = "http://localhost:11434", transport: JsonHttpTransport | None = None):
        self.base_url = base_url.rstrip("/")
        self.transport = transport or JsonHttpTransport()

    def complete(self, request: CompletionRequest) -> CompletionResponse:
        response = self.transport.post_json(
            f"{self.base_url}/api/chat",
            {"model": request.model, "messages": messages_to_openai(request.messages), "stream": False, "options": {"temperature": request.temperature}},
            {},
        )
        message = response.data.get("message") or {}
        return CompletionResponse(provider=self.name, model=request.model, content=message.get("content", ""), finish_reason="stop" if response.data.get("done") else None, raw=response.data)

    def stream(self, request: CompletionRequest) -> Iterable[StreamChunk]:
        response = self.complete(request)
        yield StreamChunk(provider=self.name, model=request.model, delta=response.content, done=True, raw=response.raw)

    def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        response = self.transport.post_json(f"{self.base_url}/api/embed", {"model": request.model, "input": request.texts}, {})
        vectors = response.data.get("embeddings")
        if vectors is None and "embedding" in response.data:
            vectors = [response.data["embedding"]]
        vectors = [[float(x) for x in vector] for vector in (vectors or [])]
        if len(vectors) != len(request.texts):
            raise ProviderError(self.name, "embedding count mismatch", retryable=True)
        return EmbeddingResponse(provider=self.name, model=request.model, vectors=vectors, raw=response.data)
