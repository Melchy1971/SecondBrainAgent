import os
import pytest


def test_openai_live_or_skip():
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("set OPENAI_API_KEY for live OpenAI embedding test")
    from secondbrain.embeddings.providers import OpenAIEmbeddingProvider
    p = OpenAIEmbeddingProvider(model="text-embedding-3-small", dimensions=1536)
    assert p.health().status == "PASS"
