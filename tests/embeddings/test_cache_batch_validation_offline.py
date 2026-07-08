import pytest
from secondbrain.embeddings.cache import EmbeddingCache, CachingEmbeddingProvider
from secondbrain.embeddings.batch import embed_batch_chunked
from secondbrain.embeddings.validation import validate_dimensions, validate_model
from secondbrain.embeddings.offline import is_offline
from secondbrain.embeddings.base import (ProviderHealth, OfflineError, DimensionMismatchError,
                                         ModelNotAllowedError)


class Counting:
    name = "fake"; model = "m"; dimensions = 3; semantic = True
    def __init__(self): self.calls = 0
    def embed(self, text): self.calls += 1; return [float(len(text)), 0.0, 0.0]
    def embed_batch(self, texts): self.calls += 1; return [[float(len(t)), 0.0, 0.0] for t in texts]
    def health(self): return ProviderHealth("PASS", self.name, self.model, 3, True, True)


def test_cache_avoids_recompute():
    prov = Counting()
    cached = CachingEmbeddingProvider(prov, EmbeddingCache())
    cached.embed("hello"); cached.embed("hello")
    assert prov.calls == 1
    assert cached.cache.stats()["hits"] == 1


def test_cache_batch_partial():
    prov = Counting(); cached = CachingEmbeddingProvider(prov)
    cached.embed("a")
    prov.calls = 0
    res = cached.embed_batch(["a", "b", "c"])
    assert len(res) == 3 and prov.calls == 1   # only 1 batch call for the 2 misses


class Flaky:
    name = "flaky"; model = "m"; dimensions = 3; semantic = True
    def __init__(self, fails): self.fails = fails; self.calls = 0
    def embed_batch(self, texts):
        self.calls += 1
        if self.calls <= self.fails:
            raise OfflineError("temporary")
        return [[1.0, 0.0, 0.0] for _ in texts]
    def embed(self, t): return self.embed_batch([t])[0]
    def health(self): return ProviderHealth("PASS", self.name, self.model, 3, True, True)


def test_batch_retries_transient():
    prov = Flaky(fails=2)
    from secondbrain.storage.db_retry import RetryPolicy
    out = embed_batch_chunked(prov, ["x", "y"], batch_size=2,
                              retry=RetryPolicy(max_attempts=5, base_delay=0), sleeper=lambda _s: None)
    assert len(out) == 2 and prov.calls == 3


def test_validation():
    validate_dimensions([[1, 2, 3]], 3)
    with pytest.raises(DimensionMismatchError):
        validate_dimensions([[1, 2]], 3)
    validate_model("m", ["m", "n"])
    with pytest.raises(ModelNotAllowedError):
        validate_model("z", ["m", "n"])


class OfflineProv:
    name = "o"; model = "m"; dimensions = 3; semantic = True
    def embed(self, t): raise OfflineError("down")
    def embed_batch(self, ts): raise OfflineError("down")
    def health(self): return ProviderHealth("FAIL", "o", "m", 3, True, False, "down")


def test_offline_detection():
    assert is_offline(OfflineProv()) is True
    assert is_offline(Counting()) is False
