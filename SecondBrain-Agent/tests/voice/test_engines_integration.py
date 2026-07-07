import pytest


def test_whisper_engine_available_or_skipped():
    pytest.importorskip("faster_whisper", reason="optional voice dep not installed")
    from secondbrain.voice.engines.whisper_stt import WhisperSttEngine
    assert WhisperSttEngine.name == "faster-whisper"


def test_piper_engine_available_or_skipped():
    pytest.importorskip("piper", reason="optional voice dep not installed")
    from secondbrain.voice.engines.piper_tts import PiperTtsEngine
    assert PiperTtsEngine.name == "piper"
