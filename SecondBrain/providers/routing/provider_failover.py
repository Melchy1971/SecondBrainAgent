"""v30.0 provider failover policy."""
from __future__ import annotations

from secondbrain.providers.base.provider_exception import ProviderError


class ProviderFailover:
    def __init__(self, providers: list[str]) -> None:
        self.providers = providers

    def candidates(self, failed: set[str] | None = None) -> list[str]:
        failed = failed or set()
        return [name for name in self.providers if name not in failed]

    def should_retry(self, error: Exception) -> bool:
        return isinstance(error, ProviderError) and error.retryable
