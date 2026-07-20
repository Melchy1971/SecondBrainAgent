from __future__ import annotations

import threading
from typing import Any, Callable


class LocalTtsRuntime:
    """Offline TTS boundary with privacy filtering and wake-feedback signalling."""

    def __init__(
        self,
        *,
        engine_factory: Callable[[], Any] | None = None,
        on_state: Callable[[bool], None] | None = None,
        voice: str = "",
        rate: int = 175,
        volume: float = 1.0,
        max_chars: int = 600,
    ) -> None:
        self._engine_factory = engine_factory or self._pyttsx3_engine
        self._on_state = on_state or (lambda _active: None)
        self.voice = voice
        self.rate = max(80, min(int(rate), 300))
        self.volume = max(0.0, min(float(volume), 1.0))
        self.max_chars = max(80, int(max_chars))
        self._engine: Any = None
        self._lock = threading.RLock()

    def speak(self, text: str, *, sensitive: bool = False, allow_sensitive: bool = False) -> dict[str, Any]:
        value = " ".join(str(text or "").split())
        if not value:
            return {"ok": False, "status": "empty", "engine": "none"}
        if sensitive and not allow_sensitive:
            return {"ok": False, "status": "sensitive_blocked", "engine": "none"}
        spoken, summarized = self._shorten(value)
        with self._lock:
            self._on_state(True)
            try:
                engine = self._engine_factory()
                self._engine = engine
                engine.setProperty("rate", self.rate)
                engine.setProperty("volume", self.volume)
                self._select_voice(engine)
                engine.say(spoken)
                engine.runAndWait()
                return {"ok": True, "status": "spoken", "engine": "pyttsx3", "summarized": summarized}
            except Exception as exc:
                return {"ok": False, "status": "error", "engine": "none", "error": f"{type(exc).__name__}: {exc}"}
            finally:
                self._engine = None
                self._on_state(False)

    def stop(self) -> bool:
        with self._lock:
            if self._engine is None:
                return False
            self._engine.stop()
            return True

    def _shorten(self, text: str) -> tuple[str, bool]:
        if len(text) <= self.max_chars:
            return text, False
        boundary = text.rfind(". ", 0, self.max_chars)
        cut = boundary + 1 if boundary >= self.max_chars // 2 else self.max_chars
        return text[:cut].rstrip() + " … Die Antwort wurde für die Sprachausgabe gekürzt.", True

    def _select_voice(self, engine: Any) -> None:
        requested = self.voice.casefold().strip()
        for candidate in engine.getProperty("voices") or []:
            blob = " ".join(str(getattr(candidate, key, "")) for key in ("id", "name", "languages")).casefold()
            if (requested and requested in blob) or (not requested and any(token in blob for token in ("german", "de-de", "de_"))):
                engine.setProperty("voice", candidate.id)
                return

    @staticmethod
    def _pyttsx3_engine() -> Any:
        import pyttsx3

        return pyttsx3.init()
