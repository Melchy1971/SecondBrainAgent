"""Validate provider payloads without exposing their contents in errors."""
import math

from .provider_exception import ProviderError


def text_content(provider, value):
    if not isinstance(value, str) or not value.strip():
        raise ProviderError(provider, "invalid_response", retryable=False)
    return value


def embedding_vectors(provider, values, expected_count):
    if not isinstance(values, list) or len(values) != expected_count:
        raise ProviderError(provider, "invalid_embedding_response", retryable=False)
    vectors = []
    dimension = None
    for row in values:
        if not isinstance(row, list) or not row:
            raise ProviderError(provider, "invalid_embedding_response", retryable=False)
        if dimension is None:
            dimension = len(row)
        if len(row) != dimension or any(isinstance(x, bool) or not isinstance(x, (int, float)) for x in row):
            raise ProviderError(provider, "invalid_embedding_response", retryable=False)
        try:
            vector = [float(x) for x in row]
        except (ValueError, OverflowError):
            raise ProviderError(provider, "invalid_embedding_response", retryable=False) from None
        if not all(math.isfinite(x) for x in vector):
            raise ProviderError(provider, "invalid_embedding_response", retryable=False)
        vectors.append(vector)
    return vectors
