import pytest
from secondbrain.embeddings.base import EmbeddingConfig, EmbeddingProviderError, ProviderHealth
from secondbrain.embeddings.factory import build_provider
from secondbrain.embeddings.gate import embedding_production_gate
from secondbrain.embeddings.reindex import reindex_needed, maybe_reindex
from secondbrain.connectors.scaffold.transport import FakeTransport


# --- SAFETY RULE 1: never silently substitute fake embeddings ---
def test_factory_never_returns_fake_for_openai():
    cfg = EmbeddingConfig(provider="openai", model="m", dimensions=4)
    p = build_provider(cfg, transport=FakeTransport())   # no route -> 404
    assert p.name == "openai"
    with pytest.raises(EmbeddingProviderError):
        p.embed("hi")                                     # raises, never returns fake


def test_factory_refuses_local_without_explicit_allow():
    cfg = EmbeddingConfig(provider="local", model="m", dimensions=8)
    with pytest.raises(EmbeddingProviderError):
        build_provider(cfg)                               # refuses silent fake
    p = build_provider(cfg, allow_local=True)
    assert p.name == "local"


# --- SAFETY RULE 2: production gate FAILs on error / non-production provider ---
class FakeProv:
    def __init__(self, health): self._h = health; self.name = health.provider
        # note: model/dimensions used by identity
    model = "m"; dimensions = 4
    def health(self): return self._h
    def embed(self, t): return [0.0] * 4
    def embed_batch(self, ts): return [[0.0] * 4 for _ in ts]


def test_gate_fails_on_health_fail():
    prov = FakeProv(ProviderHealth("FAIL", "openai", "m", 4, True, False, "boom"))
    r = embedding_production_gate(prov, environment="production")
    assert r["status"] == "FAIL"


def test_gate_fails_for_local_in_production():
    from secondbrain.embeddings.providers import LocalEmbeddingProvider
    r = embedding_production_gate(LocalEmbeddingProvider(dimensions=8), environment="production")
    assert r["status"] == "FAIL"                          # fake never PASSes in production


def test_gate_passes_healthy_semantic():
    prov = FakeProv(ProviderHealth("PASS", "openai", "m", 4, True, True))
    assert embedding_production_gate(prov, environment="production")["status"] == "PASS"


# --- automatic reindex on identity change ---
class FakeStore:
    def __init__(self): self.calls = 0
    def reindex(self, *, method="hnsw", metric="cosine"):
        self.calls += 1
        return {"backend": "fake", "status": "rebuilt", "method": method}


def test_reindex_triggers_on_identity_change():
    prov = FakeProv(ProviderHealth("PASS", "openai", "m", 4, True, True))
    store = FakeStore()
    assert reindex_needed("openai:m:4", "openai:old:4") is True
    r = maybe_reindex(prov, store, "openai:old:4")
    assert r["reindexed"] is True and store.calls == 1
    r2 = maybe_reindex(prov, store, "openai:m:4")
    assert r2["reindexed"] is False and store.calls == 1
