"""Offline detection for networked providers."""

from __future__ import annotations

from secondbrain.embeddings.base import EmbeddingProvider, OfflineError


def is_offline(provider: EmbeddingProvider) -> bool:
    """True iff a health probe fails with a connectivity error."""
    try:
        provider.embed("secondbrain offline probe")
        return False
    except OfflineError:
        return True
    except Exception:
        return False   # a non-connectivity error is not 'offline'
