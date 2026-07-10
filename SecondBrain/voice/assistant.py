"""Continuous voice assistant runtime.

Wraps the pure ``ConversationController`` (wake -> listen -> think -> speak with
barge-in) into a productive, always-on assistant:

- wake word activates listening; conversation mode keeps the turn open
- streaming TTS playback that can be interrupted mid-output (barge-in)
- microphone status + audio level for the GUI
- privacy mode (mute, no capture, no transcript retention)
- offline mode flag propagated to engine selection
- graceful handling of a missing microphone - never blocks the app
- full disable - the whole subsystem can be turned off

Hardware/models are injected via the voice ports, so the runtime is fully
unit-testable with the fakes in ``secondbrain.voice.engines.fake``.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Iterable

from secondbrain.voice.conversation import ConversationController, State
from secondbrain.voice.ports import Audio, AudioClip, MicrophoneSource


class MicStatus(str, Enum):
    OK = "ok"
    MISSING = "missing"
    MUTED = "muted"          # privacy mode
    DISABLED = "disabled"    # voice turned off
    ERROR = "error"


class MissingMicrophoneError(RuntimeError):
    """Raised by a microphone source when no capture device is available."""


def audio_level(audio: Audio) -> float:
    """Approximate 0..1 RMS level of a PCM16 chunk for the GUI meter."""
    data = audio.data or b""
    if len(data) < 2:
        return 0.0
    total = 0
    count = 0
    for i in range(0, len(data) - 1, 2):
        sample = int.from_bytes(data[i:i + 2], "little", signed=True)
        total += abs(sample)
        count += 1
    if not count:
        return 0.0
    return min(1.0, (total / count) / 32768.0)


@dataclass
class VoiceStatus:
    enabled: bool
    privacy: bool
    offline: bool
    mic_status: MicStatus
    state: str
    level: float
    last_error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "privacy": self.privacy,
            "offline": self.offline,
            "mic_status": self.mic_status.value,
            "state": self.state,
            "level": round(self.level, 4),
            "last_error": self.last_error,
        }


@dataclass
class VoiceConfig:
    enabled: bool = True
    privacy_mode: bool = False
    offline: bool = False
    conversation_mode: bool = True
    window_seconds: float = 0.5


class StreamingTtsPlayer:
    """Plays a spoken response chunk-by-chunk and can be interrupted mid-output.

    ``tts`` may be a StreamingTts (``stream(text) -> Iterator[AudioClip]``) or a
    plain TtsEngine (``synthesize(text) -> AudioClip``, treated as one chunk). The
    sink receives each chunk; ``interrupt()`` stops playback before the next chunk.
    """

    def __init__(self, tts: Any, sink: Callable[[AudioClip], None] | None = None) -> None:
        self.tts = tts
        self.sink = sink or (lambda clip: None)
        self._interrupt = threading.Event()
        self.is_playing = False
        self.played_chunks = 0
        self._thread = None

    def _chunks(self, text: str) -> Iterable[AudioClip]:
        if hasattr(self.tts, "stream"):
            return self.tts.stream(text)
        return [self.tts.synthesize(text)]

    def play(self, text: str) -> int:
        self._interrupt.clear()
        self.is_playing = True
        self.played_chunks = 0
        try:
            for clip in self._chunks(text):
                if self._interrupt.is_set():
                    break
                self.sink(clip)
                self.played_chunks += 1
        finally:
            self.is_playing = False
        return self.played_chunks

    def interrupt(self) -> None:
        self._interrupt.set()

    def play_async(self, text: str) -> "threading.Thread":
        """Play on a worker thread so capture keeps running and barge-in can interrupt."""
        thread = threading.Thread(target=self.play, args=(text,), daemon=True)
        thread.start()
        self._thread = thread
        return thread

    def wait(self, timeout: float | None = None) -> None:
        thread = getattr(self, "_thread", None)
        if thread is not None:
            thread.join(timeout=timeout)


class ContinuousVoiceAssistant:
    def __init__(
        self,
        controller: ConversationController,
        *,
        mic: MicrophoneSource | None = None,
        config: VoiceConfig | None = None,
        tts_player: StreamingTtsPlayer | None = None,
        on_status: Callable[[VoiceStatus], None] | None = None,
    ) -> None:
        self.controller = controller
        self.mic = mic
        self.config = config or VoiceConfig()
        self.tts_player = tts_player
        self.on_status = on_status
        self._mic_status = MicStatus.OK if mic is not None else MicStatus.MISSING
        self._level = 0.0
        self._last_error: str | None = None
        self._running = False
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    # --- status ---------------------------------------------------------------

    def status(self) -> VoiceStatus:
        if not self.config.enabled:
            mic = MicStatus.DISABLED
        elif self.config.privacy_mode:
            mic = MicStatus.MUTED
        else:
            mic = self._mic_status
        return VoiceStatus(
            enabled=self.config.enabled,
            privacy=self.config.privacy_mode,
            offline=self.config.offline,
            mic_status=mic,
            state=self.controller.state.value,
            level=self._level,
            last_error=self._last_error,
        )

    def _emit(self) -> None:
        if self.on_status:
            self.on_status(self.status())

    # --- controls -------------------------------------------------------------

    def set_enabled(self, enabled: bool) -> None:
        self.config.enabled = enabled
        if not enabled:
            self.stop()
        self._emit()

    def set_privacy(self, on: bool) -> None:
        self.config.privacy_mode = on
        if on and self.tts_player:
            self.tts_player.interrupt()
        self._emit()

    def set_offline(self, on: bool) -> None:
        self.config.offline = on
        self._emit()

    # --- audio ingest ---------------------------------------------------------

    def feed(self, chunk: Audio) -> list[str]:
        """Process one audio frame. Honors disabled/privacy; drives barge-in."""
        if not self.config.enabled or self.config.privacy_mode:
            self._level = 0.0
            return []
        self._level = audio_level(chunk)
        was_speaking = self.controller.state is State.SPEAKING
        events = self.controller.feed(chunk)
        # barge-in: interrupt any ongoing spoken output the moment we re-listen
        if was_speaking and "interrupted" in events and self.tts_player:
            self.tts_player.interrupt()
        if "reply" in events and self.tts_player and self.controller.turns:
            self.tts_player.play_async(self.controller.turns[-1]["assistant"])
        self._emit()
        return events

    def run_stream(self, frames: Iterable[Audio]) -> list[str]:
        out: list[str] = []
        for chunk in frames:
            out.extend(self.feed(chunk))
        return out

    # --- microphone -----------------------------------------------------------

    def probe_microphone(self) -> MicStatus:
        """Check the mic without blocking startup. Never raises."""
        if self.mic is None:
            self._mic_status = MicStatus.MISSING
            return self._mic_status
        try:
            self.mic.record(0.01)
            self._mic_status = MicStatus.OK
            self._last_error = None
        except MissingMicrophoneError as exc:
            self._mic_status = MicStatus.MISSING
            self._last_error = str(exc)
        except Exception as exc:  # noqa: BLE001 - any capture failure -> error state, app keeps running
            self._mic_status = MicStatus.ERROR
            self._last_error = str(exc)
        return self._mic_status

    def start(self) -> bool:
        """Start the capture loop on a worker thread. Returns False (not raising)
        when voice is disabled or no microphone is available."""
        if not self.config.enabled:
            self._mic_status = MicStatus.DISABLED
            self._emit()
            return False
        if self.probe_microphone() != MicStatus.OK:
            self._emit()
            return False
        with self._lock:
            if self._running:
                return True
            self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        return True

    def _loop(self) -> None:
        while self._running:
            if self.config.privacy_mode:
                continue
            try:
                chunk = self.mic.record(self.config.window_seconds)
            except MissingMicrophoneError as exc:
                self._mic_status = MicStatus.MISSING
                self._last_error = str(exc)
                self._emit()
                break
            except Exception as exc:  # noqa: BLE001 - capture failure stops the loop, not the app
                self._mic_status = MicStatus.ERROR
                self._last_error = str(exc)
                self._emit()
                break
            self.feed(chunk)

    def stop(self) -> None:
        with self._lock:
            self._running = False
        thread = self._thread
        if thread and thread.is_alive() and thread is not threading.current_thread():
            thread.join(timeout=2.0)
        self._thread = None
