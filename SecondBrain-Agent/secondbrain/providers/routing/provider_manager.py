"""v30.0 provider manager and router."""
from __future__ import annotations

from time import perf_counter
from typing import Iterable

from secondbrain.providers.base.provider_exception import ProviderError, ProviderRateLimitError
from secondbrain.providers.base.provider_models import CompletionRequest, CompletionResponse, EmbeddingRequest, EmbeddingResponse, StreamChunk
from secondbrain.providers.base.provider_protocol import ProviderProtocol
from secondbrain.providers.routing.provider_failover import ProviderFailover
from secondbrain.providers.routing.provider_metrics import ProviderMetrics
from secondbrain.providers.routing.provider_rate_limiter import ProviderRateLimiter


class ProviderManager:
    def __init__(self, rate_limiter: ProviderRateLimiter | None = None, metrics: ProviderMetrics | None = None) -> None:
        self._providers: dict[str, ProviderProtocol] = {}
        self.rate_limiter = rate_limiter or ProviderRateLimiter()
        self.metrics = metrics or ProviderMetrics()

    def register(self, provider: ProviderProtocol) -> None:
        self._providers[provider.name] = provider

    def get(self, name: str) -> ProviderProtocol:
        provider = self._providers.get(name)
        if provider is None:
            raise ProviderError(name, "provider is not registered", retryable=False)
        return provider

    def list(self) -> list[str]:
        return sorted(self._providers.keys())

    def complete(self, provider_name: str, request: CompletionRequest) -> CompletionResponse:
        provider = self.get(provider_name)
        if not self.rate_limiter.allow(provider.name):
            raise ProviderRateLimitError(provider.name, "rate limit exceeded", retryable=True, status_code=429)
        start = perf_counter()
        try:
            response = provider.complete(request)
            self.metrics.record(provider.name, "complete", (perf_counter() - start) * 1000, True)
            return response
        except Exception:
            self.metrics.record(provider.name, "complete", (perf_counter() - start) * 1000, False)
            raise

    def embed(self, provider_name: str, request: EmbeddingRequest) -> EmbeddingResponse:
        provider = self.get(provider_name)
        if not self.rate_limiter.allow(provider.name):
            raise ProviderRateLimitError(provider.name, "rate limit exceeded", retryable=True, status_code=429)
        start = perf_counter()
        try:
            response = provider.embed(request)
            self.metrics.record(provider.name, "embed", (perf_counter() - start) * 1000, True)
            return response
        except Exception:
            self.metrics.record(provider.name, "embed", (perf_counter() - start) * 1000, False)
            raise

    def complete_with_failover(self, provider_names: list[str], request: CompletionRequest) -> CompletionResponse:
        failover = ProviderFailover(provider_names)
        failed: set[str] = set()
        last_error: Exception | None = None
        for name in failover.candidates(failed):
            try:
                return self.complete(name, request)
            except Exception as exc:
                last_error = exc
                failed.add(name)
                if not failover.should_retry(exc):
                    raise
        raise ProviderError("provider_manager", f"all providers failed: {last_error}", retryable=False)

    def stream(self, provider_name: str, request: CompletionRequest) -> Iterable[StreamChunk]:
        provider = self.get(provider_name)
        yield from provider.stream(request)
