"""v30.0 Gemini chat/embedding provider."""
from __future__ import annotations

import os
from typing import Iterable

from secondbrain.providers.base.http_transport import JsonHttpTransport
from secondbrain.providers.base.provider_capabilities import ProviderCapabilities
from secondbrain.providers.base.provider_exception import ProviderConfigError, ProviderError
from secondbrain.providers.base.provider_models import CompletionRequest, CompletionResponse, EmbeddingRequest, EmbeddingResponse, StreamChunk


class GeminiProvider:
    name = "gemini"
    capabilities = ProviderCapabilities(chat=True, embeddings=True, streaming=False, local=False)

    def __init__(self, api_key: str | None = None, base_url: str = "https://generativelanguage.googleapis.com/v1beta", transport: JsonHttpTransport | None = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.base_url = base_url.rstrip("/")
        self.transport = transport or JsonHttpTransport()

    def _require_key(self) -> str:
        if not self.api_key:
            raise ProviderConfigError(self.name, "GEMINI_API_KEY is missing")
        return self.api_key

    def complete(self, request: CompletionRequest) -> CompletionResponse:
        key = self._require_key()
        contents = [{"role": "user" if m.role == "system" else m.role, "parts": [{"text": m.content}]} for m in request.messages]
        payload = {"contents": contents, "generationConfig": {"temperature": request.temperature}}
        response = self.transport.post_json(f"{self.base_url}/models/{request.model}:generateContent?key={key}", payload, {})
        candidates = response.data.get("candidates") or []
        parts = (((candidates[0] if candidates else {}).get("content") or {}).get("parts") or [])
        content = "".join(part.get("text", "") for part in parts)
        return CompletionResponse(provider=self.name, model=request.model, content=content, raw=response.data)

    def stream(self, request: CompletionRequest) -> Iterable[StreamChunk]:
        response = self.complete(request)
        yield StreamChunk(provider=self.name, model=request.model, delta=response.content, done=True, raw=response.raw)

    def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        key = self._require_key()
        vectors: list[list[float]] = []
        raw_items = []
        for text in request.texts:
            response = self.transport.post_json(
                f"{self.base_url}/models/{request.model}:embedContent?key={key}",
                {"content": {"parts": [{"text": text}]}},
                {},
            )
            raw_items.append(response.data)
            values = ((response.data.get("embedding") or {}).get("values") or [])
            vectors.append([float(x) for x in values])
        if len(vectors) != len(request.texts):
            raise ProviderError(self.name, "embedding count mismatch", retryable=False)
        return EmbeddingResponse(provider=self.name, model=request.model, vectors=vectors, raw={"items": raw_items})
