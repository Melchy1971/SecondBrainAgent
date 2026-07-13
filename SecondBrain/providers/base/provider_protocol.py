"""v30.0 unified provider protocol."""
from __future__ import annotations

from typing import Iterable, Protocol

from secondbrain.providers.base.provider_capabilities import ProviderCapabilities
from secondbrain.providers.base.provider_models import CompletionRequest, CompletionResponse, EmbeddingRequest, EmbeddingResponse, StreamChunk


class ProviderProtocol(Protocol):
    name: str
    capabilities: ProviderCapabilities

    def complete(self, request: CompletionRequest) -> CompletionResponse:
        ...

    def stream(self, request: CompletionRequest) -> Iterable[StreamChunk]:
        ...

    def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        ...
