from __future__ import annotations

import json
import os
import tempfile
from importlib.util import find_spec
from pathlib import Path
from typing import Any, Callable


def _enabled(value: str | None) -> bool:
    return str(value or "").strip().casefold() in {"1", "true", "yes", "on"}


class LocalSttPolicy:
    """Select local STT first and require explicit opt-in for cloud processing."""

    def __init__(
        self,
        *,
        environ: dict[str, str] | None = None,
        module_available: Callable[[str], bool] | None = None,
    ) -> None:
        self.environ = dict(os.environ if environ is None else environ)
        self._module_available = module_available or (lambda name: find_spec(name) is not None)

    @property
    def cloud_opt_in(self) -> bool:
        return _enabled(self.environ.get("SECONDBRAIN_CLOUD_STT_OPT_IN"))

    def status(self) -> dict[str, Any]:
        model_path = Path(self.environ.get("SECONDBRAIN_WHISPER_MODEL_PATH", ""))
        faster_whisper = self._module_available("faster_whisper") and model_path.is_dir()
        vosk_path = Path(self.environ.get("SECONDBRAIN_VOSK_MODEL_PATH", ""))
        vosk = self._module_available("vosk") and vosk_path.is_dir()
        return {
            "selected_engine": "faster_whisper" if faster_whisper else "vosk" if vosk else "google" if self.cloud_opt_in else "none",
            "faster_whisper_ready": faster_whisper,
            "vosk_ready": vosk,
            "windows_speech_ready": os.name == "nt" and self._module_available("win32com"),
            "cloud_opt_in": self.cloud_opt_in,
            "raw_audio_persisted": False,
            "model_download_allowed": False,
        }

    def transcribe(self, audio: Any, recognizer: Any, *, language: str = "de-DE") -> dict[str, Any]:
        status = self.status()
        engine = status["selected_engine"]
        if engine == "faster_whisper":
            text = self._faster_whisper(audio, language)
        elif engine == "vosk":
            text = self._vosk(audio)
        elif engine == "google":
            text = recognizer.recognize_google(audio, language=language)
        else:
            return {"ok": False, "engine": "none", "error": "Kein lokales STT-Modell verfügbar; Cloud-STT ist nicht freigegeben"}
        return {"ok": True, "engine": engine, "text": text}

    def _faster_whisper(self, audio: Any, language: str) -> str:
        from faster_whisper import WhisperModel

        model_path = Path(self.environ["SECONDBRAIN_WHISPER_MODEL_PATH"]).resolve()
        if not model_path.is_dir():
            raise RuntimeError("Lokaler Whisper-Modellpfad fehlt")
        temp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as handle:
                handle.write(audio.get_wav_data())
                temp_path = Path(handle.name)
            model = WhisperModel(str(model_path), device="cpu", compute_type="int8", local_files_only=True)
            segments, _info = model.transcribe(str(temp_path), language=language.split("-", 1)[0])
            return " ".join(segment.text.strip() for segment in segments).strip()
        finally:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)

    def _vosk(self, audio: Any) -> str:
        from vosk import KaldiRecognizer, Model

        model_path = Path(self.environ["SECONDBRAIN_VOSK_MODEL_PATH"]).resolve()
        if not model_path.is_dir():
            raise RuntimeError("Lokaler Vosk-Modellpfad fehlt")
        decoder = KaldiRecognizer(Model(str(model_path)), 16000)
        decoder.AcceptWaveform(audio.get_raw_data(convert_rate=16000, convert_width=2))
        payload = json.loads(decoder.FinalResult())
        text = str(payload.get("text") or "").strip()
        if not text:
            raise RuntimeError("Sprache nicht verstanden")
        return text
