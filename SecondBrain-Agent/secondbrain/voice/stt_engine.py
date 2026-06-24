"""Voice Control v20 - Speech-to-Text.

Echte Transkription ueber faster-whisper bzw. openai-whisper, mit
graceful Fallback. Optionale Abhaengigkeiten werden lazy importiert, damit
Modul-Import und Tests ohne installierte Audio-Stacks funktionieren.

Backward-compatible: ``SpeechToTextEngine.transcribe(chunks)`` bleibt erhalten.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

try:
    import numpy as np  # type: ignore
except Exception:  # pragma: no cover
    np = None  # type: ignore


class STTUnavailable(RuntimeError):
    """Kein echter STT-Provider verfuegbar."""


class SpeechToTextEngine:
    """Spracherkennung mit Provider-Auswahl und Fallback.

    provider: "faster_whisper" | "whisper" | "manual"
    Bei "manual" (oder fehlenden Libs) liefert ``transcribe`` weiterhin den
    zusammengefuegten Text-Chunk - so bleibt der alte Vertrag gueltig.
    """

    def __init__(self, provider: str = "faster_whisper", model: str = "small",
                 language: str = "de"):
        self.provider = provider
        self.model_name = model
        self.language = language
        self._model = None
        self._active_provider: Optional[str] = None

    # --- Verfuegbarkeit ------------------------------------------------------
    @staticmethod
    def available_providers() -> dict:
        out = {"faster_whisper": False, "whisper": False}
        try:
            import faster_whisper  # noqa: F401
            out["faster_whisper"] = True
        except Exception:
            pass
        try:
            import whisper  # noqa: F401
            out["whisper"] = True
        except Exception:
            pass
        return out

    def _ensure_model(self) -> str:
        """Laedt das Modell beim ersten Bedarf. Gibt den aktiven Provider zurueck."""
        if self._active_provider:
            return self._active_provider
        order = [self.provider] + [p for p in ("faster_whisper", "whisper")
                                   if p != self.provider]
        for prov in order:
            if prov == "faster_whisper":
                try:
                    from faster_whisper import WhisperModel  # type: ignore
                    self._model = WhisperModel(self.model_name, device="auto",
                                               compute_type="int8")
                    self._active_provider = prov
                    return prov
                except Exception:
                    continue
            elif prov == "whisper":
                try:
                    import whisper  # type: ignore
                    self._model = whisper.load_model(self.model_name)
                    self._active_provider = prov
                    return prov
                except Exception:
                    continue
        self._active_provider = "manual"
        return "manual"

    # --- Transkription -------------------------------------------------------
    def transcribe_audio(self, samples, sample_rate: int = 16000) -> str:
        """Transkribiert ein float32-Numpy-Array (mono, -1..1)."""
        prov = self._ensure_model()
        if prov == "manual" or self._model is None:
            raise STTUnavailable(
                "Kein Whisper-Provider installiert. "
                "pip install -r requirements-voice.txt"
            )
        if np is None:
            raise STTUnavailable("numpy fehlt fuer Audio-Transkription.")
        audio = np.asarray(samples, dtype="float32")
        if prov == "faster_whisper":
            segments, _ = self._model.transcribe(audio, language=self.language)
            return " ".join(seg.text for seg in segments).strip()
        # openai-whisper
        result = self._model.transcribe(audio, language=self.language, fp16=False)
        return str(result.get("text", "")).strip()

    def transcribe_file(self, path: str | Path) -> str:
        prov = self._ensure_model()
        if prov == "manual" or self._model is None:
            raise STTUnavailable("Kein Whisper-Provider installiert.")
        path = str(path)
        if prov == "faster_whisper":
            segments, _ = self._model.transcribe(path, language=self.language)
            return " ".join(seg.text for seg in segments).strip()
        result = self._model.transcribe(path, language=self.language, fp16=False)
        return str(result.get("text", "")).strip()

    def transcribe(self, chunks: list[str]) -> str:
        """Back-compat: fuegt vorliegende Text-Chunks zusammen (manueller Modus)."""
        return " ".join(c for c in chunks if c).strip()
