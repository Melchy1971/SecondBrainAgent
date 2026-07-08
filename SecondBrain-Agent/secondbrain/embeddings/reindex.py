"""Automatic reindex when the embedding provider identity changes."""

from __future__ import annotations

from secondbrain.embeddings.base import EmbeddingProvider, provider_identity


def reindex_needed(current_identity: str, stored_identity: str | None) -> bool:
    return stored_identity is None or current_identity != stored_identity


def maybe_reindex(provider: EmbeddingProvider, store, stored_identity: str | None, *,
                  method: str = "hnsw", metric: str = "cosine") -> dict:
    current = provider_identity(provider)
    if not reindex_needed(current, stored_identity):
        return {"reindexed": False, "identity": current}
    result = store.reindex(method=method, metric=metric)
    return {"reindexed": True, "identity": current, "previous": stored_identity, **result}
