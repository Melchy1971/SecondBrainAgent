import pytest
pytest.importorskip("mss", reason="vision optional dep 'mss' not installed")


def test_mss_source_constructs():
    from secondbrain.vision.engines.screen_mss import MssScreenSource
    assert MssScreenSource().name == "mss"
