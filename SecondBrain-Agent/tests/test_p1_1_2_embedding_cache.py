from __future__ import annotations

from dataclasses import dataclass

from secondbrain.rag.cache import (
    EmbeddingCacheService,
    InMemoryEmbeddingCacheRepository,
    build_embedding_cache_key,
    normalize_cache_text,
)


@dataclass
class CountingProvider:
    name: str = "deterministic"
    model: str | None = "unit-test"
    calls: int = 0

    def embed(self, texts: list[str]) -> list[list[float]]:
        self.calls += 1
        return [[float(len(text)), float(index)] for index, text in enumerate(texts)]


def test_cache_key_is_provider_and_model_isolated() -> None:
    text = "  Alpha   Beta  "
    key_a = build_embedding_cache_key(text, provider="ollama", model="nomic")
    key_b = build_embedding_cache_key(text, provider="openai", model="nomic")
    key_c = build_embedding_cache_key(text, provider="ollama", model="other")

    assert key_a != key_b
    assert key_a != key_c
    assert build_embedding_cache_key("Alpha Beta", provider="ollama", model="nomic") == key_a


def test_normalize_cache_text_preserves_case_but_collapses_whitespace() -> None:
    assert normalize_cache_text("  Hello\nWorld\tX  ") == "Hello World X"
    assert normalize_cache_text("hello") != normalize_cache_text("Hello")


def test_embed_texts_uses_provider_only_for_misses() -> None:
    repo = InMemoryEmbeddingCacheRepository()
    cache = EmbeddingCacheService(repo)
    provider = CountingProvider()

    first = cache.embed_texts(["one", "two"], provider)
    second = cache.embed_texts(["one", "two"], provider)

    assert first == [[3.0, 0.0], [3.0, 1.0]]
    assert second == first
    assert provider.calls == 1
    assert cache.stats().hits == 2
    assert cache.stats().misses == 2
    assert cache.stats().writes == 2
    assert cache.stats().entries == 2
    assert cache.stats().hit_rate == 0.5


def test_cache_returns_defensive_vector_copy() -> None:
    repo = InMemoryEmbeddingCacheRepository()
    cache = EmbeddingCacheService(repo)
    provider = CountingProvider()

    cache.put("x", [1.0, 2.0], provider)
    vector = cache.get("x", provider)
    assert vector == [1.0, 2.0]

    vector.append(99.0)  # type: ignore[union-attr]

    assert cache.get("x", provider) == [1.0, 2.0]


def test_cache_invalidate_removes_single_provider_model_entry() -> None:
    repo = InMemoryEmbeddingCacheRepository()
    cache = EmbeddingCacheService(repo)
    provider = CountingProvider()

    cache.put("x", [1.0], provider)
    assert cache.invalidate("x", provider) is True
    assert cache.invalidate("x", provider) is False
    assert cache.get("x", provider) is None
