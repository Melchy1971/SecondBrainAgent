from secondbrain.desktop_native.action_registry import build_core_registry
from secondbrain.desktop_native.voice_runtime import VoiceSession
from secondbrain.desktop_native.wake_word import WakeWordConfig, WakeWordRuntime


def test_activation_callback_runs_once_after_policy_accepts_phrase():
    calls = []
    session = VoiceSession(build_core_registry(lambda payload: payload))
    runtime = WakeWordRuntime(
        session,
        lambda: "",
        config=WakeWordConfig(enabled=True, cooldown_seconds=10),
        clock=lambda: 100.0,
        on_activation=calls.append,
    )
    assert runtime.process_phrase("Hey Jarvis") is True
    assert runtime.process_phrase("Hey Jarvis") is False
    assert calls == ["hey jarvis"]


def test_runtime_can_be_enabled_and_disabled_from_tray_model():
    session = VoiceSession(build_core_registry(lambda payload: payload))
    runtime = WakeWordRuntime(session, lambda: "", config=WakeWordConfig(poll_interval_seconds=0.01))
    assert runtime.enable(True) is True
    assert runtime.status()["enabled"] is True
    runtime.enable(False)
    assert runtime.status()["enabled"] is False
    assert runtime.running is False
