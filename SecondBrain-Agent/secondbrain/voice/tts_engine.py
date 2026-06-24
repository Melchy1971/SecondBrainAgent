"""Voice Control v20 - Text-to-Speech.

Sprachausgabe ueber pyttsx3 (nutzt unter Windows SAPI5). Faellt auf
Konsolen-Ausgabe zurueck, wenn keine TTS-Engine verfuegbar ist.

Backward-compatible: ``TextToSpeechEngine.synthesize(text) -> bytes`` bleibt.
"""
from __future__ import annotations

from typing import Optional


class TextToSpeechEngine:
    """Sprachausgabe mit Provider-Auswahl und Konsolen-Fallback.

    provider: "pyttsx3" | "sapi" | "console"
    """

    def __init__(self, provider: str = "pyttsx3", rate: int = 185,
                 language: str = "de"):
        self.provider = provider
        self.rate = rate
        self.language = language
        self._engine = None
        self._active_provider: Optional[str] = None

    @staticmethod
    def available_providers() -> dict:
        out = {"pyttsx3": False, "sapi": False}
        try:
            import pyttsx3  # noqa: F401
            out["pyttsx3"] = True
        except Exception:
            pass
        try:  # SAPI direkt (nur Windows)
            import win32com.client  # noqa: F401
            out["sapi"] = True
        except Exception:
            pass
        return out

    def _ensure_engine(self) -> str:
        if self._active_provider:
            return self._active_provider
        if self.provider in ("pyttsx3", "sapi"):
            try:
                import pyttsx3  # type: ignore
                self._engine = pyttsx3.init()
                try:
                    self._engine.setProperty("rate", self.rate)
                    for v in self._engine.getProperty("voices"):
                        meta = f"{getattr(v, 'id', '')} {getattr(v, 'name', '')}".lower()
                        if self.language[:2] in meta or "german" in meta or "de-" in meta:
                            self._engine.setProperty("voice", v.id)
                            break
                except Exception:
                    pass
                self._active_provider = "pyttsx3"
                return "pyttsx3"
            except Exception:
                pass
        self._active_provider = "console"
        return "console"

    def speak(self, text: str) -> str:
        """Spricht den Text. Gibt den verwendeten Provider zurueck."""
        text = (text or "").strip()
        if not text:
            return self._active_provider or "console"
        prov = self._ensure_engine()
        if prov == "pyttsx3" and self._engine is not None:
            try:
                self._engine.say(text)
                self._engine.runAndWait()
                return prov
            except Exception:
                self._active_provider = "console"
        print(f"[Jarvis] {text}")
        return "console"

    def synthesize(self, text: str) -> bytes:
        """Back-compat: liefert die UTF-8-Bytes des Textes."""
        return (text or "").encode("utf-8")
