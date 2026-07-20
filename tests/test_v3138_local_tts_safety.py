from secondbrain.desktop_native.action_registry import build_core_registry
from secondbrain.desktop_native.tts import LocalTtsRuntime
from secondbrain.desktop_native.voice_runtime import VoiceSession, VoiceState


class FakeEngine:
    def __init__(self):
        self.properties = {}
        self.spoken = []
        self.stopped = False

    def setProperty(self, key, value):
        self.properties[key] = value

    def getProperty(self, key):
        return []

    def say(self, text):
        self.spoken.append(text)

    def runAndWait(self):
        pass

    def stop(self):
        self.stopped = True


def test_sensitive_text_is_not_sent_to_engine_without_opt_in():
    calls = []
    runtime = LocalTtsRuntime(engine_factory=lambda: calls.append(True))
    result = runtime.speak("Vertrauliche E-Mail", sensitive=True)
    assert result["status"] == "sensitive_blocked"
    assert calls == []


def test_tts_state_blocks_wake_word_and_resets_after_speech():
    session = VoiceSession(build_core_registry(lambda payload: payload))
    engine = FakeEngine()
    observed = []

    def state(active):
        session.set_speaking(active)
        observed.append((active, session.wake("Jarvis") if active else None))

    result = LocalTtsRuntime(engine_factory=lambda: engine, on_state=state).speak("Status ist grün")
    assert result["ok"] is True
    assert observed[0] == (True, False)
    assert session.state == VoiceState.IDLE
    assert session.wake("Jarvis") is True


def test_long_output_is_summarized_and_settings_are_bounded():
    engine = FakeEngine()
    runtime = LocalTtsRuntime(engine_factory=lambda: engine, rate=999, volume=5, max_chars=80)
    result = runtime.speak("Ein langer Satz. " * 20)
    assert result["summarized"] is True
    assert len(engine.spoken[0]) < 180
    assert engine.properties["rate"] == 300
    assert engine.properties["volume"] == 1.0
