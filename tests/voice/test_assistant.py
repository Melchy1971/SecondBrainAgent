"""Tests for the continuous voice assistant (Task 6)."""

from __future__ import annotations

import struct

from secondbrain.voice.assistant import (
    ContinuousVoiceAssistant,
    MicStatus,
    MissingMicrophoneError,
    StreamingTtsPlayer,
    VoiceConfig,
    audio_level,
)
from secondbrain.voice.conversation import ConversationController, State
from secondbrain.voice.engines.fake import FakeStreamingStt, FakeTtsEngine, FakeVad, FakeWakeWord
from secondbrain.voice.ports import Audio, AudioClip


def _wake() -> Audio:
    return Audio(data=b"WAKE")


def _speech(text: str) -> Audio:
    return Audio(data=b"S:" + text.encode("utf-8"))


def _sil() -> Audio:
    return Audio(data=b"...")


def _controller(responder=lambda t: f"reply:{t}") -> ConversationController:
    return ConversationController(
        wake=FakeWakeWord(), vad=FakeVad(), stt_factory=FakeStreamingStt,
        tts=FakeTtsEngine(), responder=responder,
    )


class _MultiChunkTts:
    """Streaming TTS that yields several chunks per utterance."""

    def __init__(self, chunks: int = 5) -> None:
        self.chunks = chunks

    def stream(self, text: str):
        for i in range(self.chunks):
            yield AudioClip(data=f"c{i}".encode(), sample_rate=22050, format="wav")


class _SpyPlayer:
    def __init__(self) -> None:
        self.plays: list[str] = []
        self.interrupts = 0

    def play_async(self, text: str):
        self.plays.append(text)

    def interrupt(self) -> None:
        self.interrupts += 1


class _MissingMic:
    def record(self, seconds: float) -> Audio:
        raise MissingMicrophoneError("no capture device")


# --- wake word / turn ----------------------------------------------------------

def test_wake_word_activates_listening():
    a = ContinuousVoiceAssistant(_controller())
    events = a.feed(_wake())
    assert "listening" in events
    assert a.controller.state is State.LISTENING


def test_full_turn_produces_reply_and_plays_tts():
    player = StreamingTtsPlayer(FakeTtsEngine())
    a = ContinuousVoiceAssistant(_controller(), tts_player=player)
    events = a.run_stream([_wake(), _speech("hallo"), _sil(), _sil()])
    assert "reply" in events
    player.wait(timeout=2.0)
    assert a.controller.turns and a.controller.turns[-1]["user"] == "hallo"
    assert player.played_chunks >= 1


# --- streaming interrupt (barge-in core) --------------------------------------

def test_streaming_tts_can_be_interrupted_mid_output():
    player = StreamingTtsPlayer(_MultiChunkTts(chunks=5))
    received = []

    def sink(clip):
        received.append(clip)
        if len(received) == 2:
            player.interrupt()

    player.sink = sink
    played = player.play("lange antwort")
    assert played == 2  # stopped after interrupt, not all 5 chunks


def test_barge_in_calls_interrupt_on_player():
    spy = _SpyPlayer()
    a = ContinuousVoiceAssistant(_controller(), tts_player=spy)
    a.run_stream([_wake(), _speech("hallo"), _sil(), _sil()])  # -> SPEAKING, play_async
    assert spy.plays
    a.feed(_speech("stop"))  # barge-in during SPEAKING
    assert spy.interrupts >= 1


# --- missing microphone --------------------------------------------------------

def test_missing_microphone_does_not_block_app():
    a = ContinuousVoiceAssistant(_controller(), mic=None)
    assert a.probe_microphone() is MicStatus.MISSING
    assert a.start() is False              # does not raise, app keeps running
    assert a.feed(_wake())                 # feeding provided frames still works


def test_microphone_error_is_captured():
    a = ContinuousVoiceAssistant(_controller(), mic=_MissingMic())
    assert a.probe_microphone() is MicStatus.MISSING
    assert a.status().last_error


# --- disable / privacy ---------------------------------------------------------

def test_voice_can_be_fully_disabled():
    a = ContinuousVoiceAssistant(_controller(), config=VoiceConfig(enabled=False))
    assert a.feed(_wake()) == []
    assert a.controller.state is State.IDLE
    assert a.status().mic_status is MicStatus.DISABLED
    assert a.start() is False


def test_privacy_mode_mutes_capture():
    a = ContinuousVoiceAssistant(_controller(), config=VoiceConfig(privacy_mode=True))
    assert a.feed(_speech("secret")) == []
    assert a.controller.turns == []
    assert a.status().mic_status is MicStatus.MUTED
    assert a.status().level == 0.0


# --- audio level / status ------------------------------------------------------

def test_audio_level_reflects_amplitude():
    loud = Audio(data=struct.pack("<10h", *([30000] * 10)))
    quiet = Audio(data=struct.pack("<10h", *([0] * 10)))
    assert audio_level(loud) > 0.5
    assert audio_level(quiet) == 0.0


def test_status_snapshot_fields():
    a = ContinuousVoiceAssistant(_controller(), config=VoiceConfig(offline=True))
    snap = a.status().to_dict()
    assert snap["offline"] is True
    assert set(snap) >= {"enabled", "privacy", "offline", "mic_status", "state", "level"}
