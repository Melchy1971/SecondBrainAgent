"""Offline TTS via Piper. Lazy deps; integration-only."""

from __future__ import annotations

import io
import wave

from secondbrain.voice.ports import AudioClip


class PiperTtsEngine:
    name = "piper"

    def __init__(self, model_path: str) -> None:
        try:
            from piper.voice import PiperVoice  # noqa: F401
        except Exception as exc:  # pragma: no cover - only without optional deps
            raise RuntimeError(
                "PiperTtsEngine requires optional dep 'piper-tts': pip install -r requirements-voice.txt"
            ) from exc
        from piper.voice import PiperVoice
        self.voice = PiperVoice.load(model_path)

    def synthesize(self, text: str) -> AudioClip:  # pragma: no cover - integration
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wav:
            self.voice.synthesize(text, wav)
        data = buf.getvalue()
        return AudioClip(data=data, sample_rate=getattr(self.voice.config, "sample_rate", 22050), format="wav")
