"""Offline STT via faster-whisper (GPU). Lazy deps; integration-only."""

from __future__ import annotations

import tempfile
from pathlib import Path

from secondbrain.voice.ports import Audio, Transcript, TranscriptSegment


class WhisperSttEngine:
    name = "faster-whisper"

    def __init__(self, model_size: str = "base", *, device: str = "cuda", compute_type: str = "float16") -> None:
        try:
            from faster_whisper import WhisperModel  # noqa: F401
        except Exception as exc:  # pragma: no cover - only without optional deps
            raise RuntimeError(
                "WhisperSttEngine requires optional dep 'faster-whisper': "
                "pip install -r requirements-voice.txt"
            ) from exc
        from faster_whisper import WhisperModel
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)

    def transcribe(self, audio: Audio, *, lang: str | None = None) -> Transcript:  # pragma: no cover - integration
        path = audio.source_uri
        tmp = None
        if not path or not path.startswith("file:"):
            tmp = tempfile.NamedTemporaryFile(suffix=f".{audio.format}", delete=False)
            tmp.write(audio.data)
            tmp.flush()
            src = tmp.name
        else:
            src = path.replace("file://", "")
        try:
            segments, info = self.model.transcribe(src, language=lang)
            segs = [TranscriptSegment(text=s.text, start=s.start, end=s.end,
                                      confidence=getattr(s, "avg_logprob", 0.0))
                    for s in segments]
            return Transcript.from_segments(segs, language=getattr(info, "language", lang or "en"))
        finally:
            if tmp is not None:
                Path(tmp.name).unlink(missing_ok=True)
