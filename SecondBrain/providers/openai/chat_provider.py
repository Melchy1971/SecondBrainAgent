"""v30.0 OpenAI chat/embedding provider.

Implements the unified provider protocol via OpenAI-compatible HTTP endpoints.
API key is read from OPENAI_API_KEY unless supplied explicitly.
"""
from __future__ import annotations

import os
from typing import Iterable

from secondbrain.providers.base.http_transport import JsonHttpTransport
from secondbrain.providers.base.response_validation import text_content, embedding_vectors
from secondbrain.providers.base.provider_capabilities import ProviderCapabilities
from secondbrain.providers.base.provider_exception import ProviderConfigError, ProviderError
from secondbrain.providers.base.provider_models import CompletionRequest, CompletionResponse, EmbeddingRequest, EmbeddingResponse, StreamChunk, messages_to_openai


class OpenAIProvider:
    name = "openai"
    capabilities = ProviderCapabilities(chat=True, embeddings=True, streaming=False, local=False, supports_json_mode=True)

    def __init__(self, api_key: str | None = None, base_url: str = "https://api.openai.com/v1", transport: JsonHttpTransport | None = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url.rstrip("/")
        self.transport = transport or JsonHttpTransport()

    def _headers(self) -> dict[str, str]:
        if not self.api_key:
            raise ProviderConfigError(self.name, "OPENAI_API_KEY is missing")
        return {"Authorization": f"Bearer {self.api_key}"}

    def complete(self, request: CompletionRequest) -> CompletionResponse:
        payload = {
            "model": request.model,
            "messages": messages_to_openai(request.messages),
            "temperature": request.temperature,
        }
        if request.max_tokens is not None:
            payload["max_tokens"] = request.max_tokens
        if request.response_format == "json_object":
            payload["response_format"] = {"type": "json_object"}
        response = self.transport.post_json(f"{self.base_url}/chat/completions", payload, self._headers())
        choices = response.data.get("choices")
        if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
            raise ProviderError(self.name, "invalid_response", retryable=False)
        choice = choices[0]
        message = choice.get("message")
        if not isinstance(message, dict):
            raise ProviderError(self.name, "invalid_response", retryable=False)
        return CompletionResponse(
            provider=self.name,
            model=request.model,
            content=text_content(self.name, message.get("content")),
            finish_reason=choice.get("finish_reason"),
            usage=response.data.get("usage", {}),
            raw=response.data,
        )

    def stream(self, request: CompletionRequest) -> Iterable[StreamChunk]:
        # stdlib streaming SSE support is intentionally not enabled here. The
        # adapter remains protocol-compatible and returns a single deterministic
        # chunk for callers that require streaming iteration.
        response = self.complete(request)
        yield StreamChunk(provider=self.name, model=request.model, delta=response.content, done=True, raw=response.raw)

    def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        response = self.transport.post_json(
            f"{self.base_url}/embeddings",
            {"model": request.model, "input": request.texts},
            self._headers(),
        )
        data = response.data.get("data")
        if not isinstance(data, list) or any(not isinstance(item, dict) for item in data):
            raise ProviderError(self.name, "invalid_embedding_response", retryable=False)
        vectors = embedding_vectors(self.name, [item.get("embedding") for item in data], len(request.texts))
        if len(vectors) != len(request.texts):
            raise ProviderError(self.name, "embedding count mismatch", retryable=False)
        return EmbeddingResponse(provider=self.name, model=request.model, vectors=vectors, usage=response.data.get("usage", {}), raw=response.data)
