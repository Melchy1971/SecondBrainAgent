"""v30.0 provider exceptions."""
from __future__ import annotations


class ProviderError(RuntimeError):
    def __init__(self, provider: str, message: str, *, retryable: bool = False, status_code: int | None = None, error_code: str | None = None):
        super().__init__(f"{provider}: {message}")
        self.provider = provider
        self.retryable = retryable
        self.status_code = status_code
        self.error_code = error_code


class ProviderConfigError(ProviderError):
    pass


class ProviderRateLimitError(ProviderError):
    pass


class ProviderTimeoutError(ProviderError):
    pass
