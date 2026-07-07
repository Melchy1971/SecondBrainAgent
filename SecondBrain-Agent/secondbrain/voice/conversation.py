"""Conversation controller: wake -> listen -> think -> speak, with barge-in interrupt.

Pure state machine over audio frames. Hardware/models are injected (wake detector,
VAD, streaming STT factory, TTS, responder). Fully deterministic and unit-testable.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Callable

from secondbrain.voice.ports import Audio, TtsEngine, WakeWordDetector, VoiceActivityDetector, StreamingStt
from secondbrain.voice.streaming import StreamingSttSession


class State(str, Enum):
    IDLE = "idle"          # waiting for wake word
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"


class ConversationController:
    def __init__(
        self,
        wake: WakeWordDetector,
        vad: VoiceActivityDetector,
        stt_factory: Callable[[], StreamingStt],
        tts: TtsEngine,
        responder: Callable[[str], str],
        *,
        conversation_mode: bool = True,
        end_silence_frames: int = 2,
        speaking_frames: int = 2,
    ) -> None:
        self.wake = wake
        self.vad = vad
        self.stt_factory = stt_factory
        self.tts = tts
        self.responder = responder
        self.conversation_mode = conversation_mode
        self.end_silence_frames = end_silence_frames
        self.speaking_frames = speaking_frames

        self.state = State.IDLE
        self.turns: list[dict[str, str]] = []
        self._session: StreamingSttSession | None = None
        self._speaking_left = 0
        self._last_audio = None

    def feed(self, chunk: Audio) -> list[str]:
        events: list[str] = []
        if self.state is State.IDLE:
            if self.wake.process(chunk):
                self._enter_listening(events)
            return events

        if self.state is State.LISTENING:
            result = self._session.feed(chunk)
            if result["partials"]:
                events.append("partial")
            if result["final"] is not None:
                events.append("final")
                self._think_and_speak(result["final"].text, events)
            return events

        if self.state is State.SPEAKING:
            # barge-in: user starts speaking while assistant talks -> interrupt
            if self.vad.is_speech(chunk):
                events.append("interrupted")
                self._enter_listening(events)
                self._session.feed(chunk)  # capture the interrupting speech
                return events
            self._speaking_left -= 1
            if self._speaking_left <= 0:
                events.append("spoke")
                if self.conversation_mode:
                    self._enter_listening(events)
                else:
                    self.state = State.IDLE
                    events.append("idle")
            return events

        return events

    # ---- transitions ------------------------------------------------------
    def _enter_listening(self, events: list[str]) -> None:
        self.state = State.LISTENING
        self._session = StreamingSttSession(self.stt_factory, self.vad,
                                            end_silence_frames=self.end_silence_frames)
        events.append("listening")

    def _think_and_speak(self, text: str, events: list[str]) -> None:
        self.state = State.THINKING
        reply = self.responder(text)
        self.turns.append({"user": text, "assistant": reply})
        self._last_audio = self.tts.synthesize(reply)
        self.state = State.SPEAKING
        self._speaking_left = self.speaking_frames
        events.append("reply")

    def run(self, frames) -> list[str]:
        out: list[str] = []
        for chunk in frames:
            out.extend(self.feed(chunk))
        return out
