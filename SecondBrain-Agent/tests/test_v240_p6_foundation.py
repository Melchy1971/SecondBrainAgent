from secondbrain.voice.stt_engine import SpeechToTextEngine
from secondbrain.voice.wake_word_engine import WakeWordEngine
from secondbrain.voice.command_router import VoiceCommandRouter


def test_stt():
    assert SpeechToTextEngine().transcribe(["Hallo", "Welt"]) == "Hallo Welt"


def test_wake_word():
    assert WakeWordEngine().detect("Hallo Jarvis")


def test_router():
    assert VoiceCommandRouter().route("öffne mail") == "gmail"
