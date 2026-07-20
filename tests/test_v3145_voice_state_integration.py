import inspect

import pytest

from secondbrain.desktop_native.action_registry import build_core_registry
from secondbrain.desktop_native.voice_de import GermanVoiceController
from secondbrain.desktop_native.voice_runtime import VoiceSession, VoiceState


def _session():
    return VoiceSession(build_core_registry(lambda payload: payload))


def test_audio_lifecycle_reaches_transcribing_and_understanding():
    session = _session()
    assert session.set_audio_state("LISTENING") is VoiceState.LISTENING
    assert session.set_audio_state("TRANSCRIBING") is VoiceState.TRANSCRIBING
    result = session.dispatch("assistant.ask", {"text": "Hallo"})
    assert result["status"] == "executed"
    assert session.state is VoiceState.IDLE


def test_audio_adapter_cannot_override_privacy_guards():
    session = _session()
    session.mute()
    assert session.set_audio_state("LISTENING") is VoiceState.MUTED
    session.mute(False)
    session.set_speaking(True)
    assert session.set_audio_state("TRANSCRIBING") is VoiceState.SPEAKING


def test_audio_adapter_rejects_non_audio_states():
    session = _session()
    with pytest.raises(ValueError, match="invalid audio state"):
        session.set_audio_state("EXECUTING")


def test_audio_failure_is_visible():
    session = _session()
    assert session.set_audio_state("ERROR") is VoiceState.ERROR


def test_wake_probes_can_disable_user_visible_state_reporting():
    signature = inspect.signature(GermanVoiceController.listen_once)
    assert signature.parameters["report_state"].default is True
