import threading

from secondbrain.desktop_native.action_registry import build_core_registry
from secondbrain.desktop_native.voice_runtime import VoiceSession, VoiceState
from secondbrain.desktop_native.wake_word import WakeWordConfig, WakeWordRuntime


def session():
    return VoiceSession(build_core_registry(lambda payload: payload))


def test_disabled_runtime_does_not_start():
    runtime = WakeWordRuntime(session(), lambda: "Jarvis")
    assert runtime.start() is False
    assert runtime.status()["raw_audio_persisted"] is False


def test_cooldown_prevents_duplicate_activation():
    ticks = iter((10.0, 10.5, 13.0))
    active = session()
    runtime = WakeWordRuntime(active, lambda: "", config=WakeWordConfig(enabled=True, cooldown_seconds=2), clock=lambda: next(ticks))
    assert runtime.process_phrase("Jarvis") is True
    active.state = VoiceState.LISTENING_FOR_WAKE_WORD
    assert runtime.process_phrase("Jarvis") is False
    assert runtime.process_phrase("Hey Jarvis") is True
    assert runtime.activations == 2


def test_tts_and_mute_block_activation():
    active = session()
    runtime = WakeWordRuntime(active, lambda: "", config=WakeWordConfig(enabled=True))
    active.set_speaking(True)
    assert runtime.process_phrase("Jarvis") is False
    active.set_speaking(False)
    active.mute()
    assert runtime.process_phrase("Jarvis") is False


def test_worker_stops_cleanly_after_activation():
    active = session()
    heard = threading.Event()

    def source():
        heard.set()
        return "SecondBrain"

    runtime = WakeWordRuntime(active, source, config=WakeWordConfig(enabled=True, poll_interval_seconds=0.01))
    assert runtime.start() is True
    assert heard.wait(1)
    runtime.stop()
    assert runtime.running is False
    assert runtime.activations == 1
