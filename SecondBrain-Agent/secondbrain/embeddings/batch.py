"""Batched embedding requests with retry + backoff (reuses storage.db_retry)."""

from __future__ import annotations

import time
from typing import Callable

from secondbrain.storage.db_retry import RetryPolicy, run_with_retry, is_transient
from secondbrain.embeddings.base import EmbeddingProvider, OfflineError


def _transient(exc: BaseException) -> bool:
    return isinstance(exc, OfflineError) or is_transient(exc)


def embed_batch_chunked(provider: EmbeddingProvider, texts: list[str], *,
                        batch_size: int = 128, retry: RetryPolicy | None = None,
                        sleeper: Callable[[float], None] = time.sleep) -> list[list[float]]:
    if batch_size < 1:
        raise ValueError("batch_size must be >= 1")
    retry = retry or RetryPolicy()
    out: list[list[float]] = []
    for start in range(0, len(texts), batch_size):
        chunk = texts[start:start + batch_size]
        vectors = run_with_retry(lambda c=chunk: provider.embed_batch(c), retry,
                                 transient=_transient, sleeper=sleeper)
        out.extend(vectors)
    return out
