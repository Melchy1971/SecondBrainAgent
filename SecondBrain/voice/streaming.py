"""Streaming STT session with VAD endpointing (deterministic, unit-testable)."""

from __future__ import annotations

from typing import Any, Callable

from secondbrain.voice.ports import Audio, Transcript, StreamingStt, VoiceActivityDetector


class StreamingSttSession:
    """Feeds audio chunks to a StreamingStt engine and endpoints on trailing silence.

    stt_factory is called to (re)create a fresh streaming engine per utterance, so
    finalize() cleanly resets state between turns.
    """

    def __init__(self, stt_factory: Callable[[], StreamingStt], vad: VoiceActivityDetector,
                 *, end_silence_frames: int = 2) -> None:
        self.stt_factory = stt_factory
        self.vad = vad
        self.end_silence_frames = end_silence_frames
        self._stt = stt_factory()
        self._had_speech = False
        self._silence = 0

    def feed(self, chunk: Audio) -> dict[str, Any]:
        if self.vad.is_speech(chunk):
            partials = self._stt.push(chunk)
            self._had_speech = True
            self._silence = 0
            return {"partials": partials, "final": None, "speaking": True}
        self._silence += 1
        if self._had_speech and self._silence >= self.end_silence_frames:
            transcript = self._stt.finalize()
            self._reset()
            return {"partials": [], "final": transcript, "speaking": False}
        return {"partials": [], "final": None, "speaking": False}

    def _reset(self) -> None:
        self._stt = self.stt_factory()
        self._had_speech = False
        self._silence = 0
