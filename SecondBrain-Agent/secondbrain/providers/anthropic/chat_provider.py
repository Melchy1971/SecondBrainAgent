"""v30.0 Anthropic chat provider."""
from __future__ import annotations

import os
from typing import Iterable

from secondbrain.providers.base.http_transport import JsonHttpTransport
from secondbrain.providers.base.provider_capabilities import ProviderCapabilities
from secondbrain.providers.base.provider_exception import ProviderConfigError, ProviderError
from secondbrain.providers.base.provider_models import CompletionRequest, CompletionResponse, EmbeddingRequest, EmbeddingResponse, StreamChunk


class AnthropicProvider:
    name = "anthropic"
    capabilities = ProviderCapabilities(chat=True, embeddings=False, streaming=False, local=False)

    def __init__(self, api_key: str | None = None, base_url: str = "https://api.anthropic.com/v1", transport: JsonHttpTransport | None = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.base_url = base_url.rstrip("/")
        self.transport = transport or JsonHttpTransport()

    def _headers(self) -> dict[str, str]:
        if not self.api_key:
            raise ProviderConfigError(self.name, "ANTHROPIC_API_KEY is missing")
        return {"x-api-key": self.api_key, "anthropic-version": "2023-06-01"}

    def complete(self, request: CompletionRequest) -> CompletionResponse:
        system = "\n".join(m.content for m in request.messages if m.role == "system")
        messages = [{"role": m.role, "content": m.content} for m in request.messages if m.role != "system"]
        payload = {
            "model": request.model,
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens or 1024,
        }
        if system:
            payload["system"] = system
        response = self.transport.post_json(f"{self.base_url}/messages", payload, self._headers())
        blocks = response.data.get("content") or []
        content = "".join(block.get("text", "") for block in blocks if block.get("type") == "text")
        return CompletionResponse(provider=self.name, model=request.model, content=content, finish_reason=response.data.get("stop_reason"), usage=response.data.get("usage", {}), raw=response.data)

    def stream(self, request: CompletionRequest) -> Iterable[StreamChunk]:
        response = self.complete(request)
        yield StreamChunk(provider=self.name, model=request.model, delta=response.content, done=True, raw=response.raw)

    def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        raise ProviderError(self.name, "Anthropic embeddings are not supported by this adapter", retryable=False)
