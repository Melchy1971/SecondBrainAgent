from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass

from .voice_runtime import VoiceSession, VoiceState


@dataclass(frozen=True, slots=True)
class WakeWordConfig:
    phrases: tuple[str, ...] = ("jarvis", "hey jarvis", "secondbrain")
    enabled: bool = False
    cooldown_seconds: float = 2.0
    poll_interval_seconds: float = 0.25


class WakeWordRuntime:
    """Low-frequency local wake loop; phrase providers own transient audio capture."""

    def __init__(
        self,
        session: VoiceSession,
        phrase_source: Callable[[], str],
        *,
        config: WakeWordConfig | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.session = session
        self.phrase_source = phrase_source
        self.config = config or WakeWordConfig()
        self.clock = clock
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._last_activation = float("-inf")
        self.activations = 0

    def start(self) -> bool:
        if not self.config.enabled or self.running:
            return False
        self._stop.clear()
        self.session.listen_for_wake_word()
        self._thread = threading.Thread(target=self._run, name="jarvis-wake-word", daemon=True)
        self._thread.start()
        return True

    def stop(self, timeout: float = 2.0) -> None:
        self._stop.set()
        thread = self._thread
        if thread and thread is not threading.current_thread():
            thread.join(timeout=max(0.0, timeout))
        self._thread = None
        if self.session.state == VoiceState.LISTENING_FOR_WAKE_WORD:
            self.session.listen_for_wake_word(False)

    @property
    def running(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    def process_phrase(self, phrase: str) -> bool:
        normalized = " ".join(str(phrase or "").casefold().split())
        if normalized not in {" ".join(item.casefold().split()) for item in self.config.phrases}:
            return False
        now = self.clock()
        if now - self._last_activation < self.config.cooldown_seconds:
            return False
        if not self.session.wake(normalized):
            return False
        self._last_activation = now
        self.activations += 1
        return True

    def status(self) -> dict[str, object]:
        return {
            "enabled": self.config.enabled,
            "running": self.running,
            "phrases": list(self.config.phrases),
            "cooldown_seconds": self.config.cooldown_seconds,
            "activations": self.activations,
            "raw_audio_persisted": False,
            "local_only": True,
        }

    def _run(self) -> None:
        while not self._stop.wait(self.config.poll_interval_seconds):
            if self.session.tts_active or self.session.state == VoiceState.MUTED:
                continue
            try:
                self.process_phrase(self.phrase_source())
            except Exception:
                # Missing microphones and transient local-engine errors keep the
                # desktop alive in degraded mode; diagnostics expose no audio.
                continue
