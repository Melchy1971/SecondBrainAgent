import pytest


def test_webrtcvad_or_skip():
    pytest.importorskip("webrtcvad")
    from secondbrain.voice.engines.webrtc_vad import WebRtcVad
    assert WebRtcVad(2) is not None


def test_openwakeword_or_skip():
    pytest.importorskip("openwakeword")
    from secondbrain.voice.engines.openwakeword_detector import OpenWakeWordDetector
    assert OpenWakeWordDetector.name == "openwakeword"
