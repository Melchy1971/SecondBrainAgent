import pytest


def test_resemblyzer_or_skip():
    pytest.importorskip("resemblyzer")
    from secondbrain.voice.engines.resemblyzer_embedder import ResemblyzerEmbedder
    assert ResemblyzerEmbedder.name == "resemblyzer"
