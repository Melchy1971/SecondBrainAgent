"""Chunked streaming STT over faster-whisper (offline). Lazy dep; integration-only.

Buffers pushed audio and transcribes the accumulated buffer on finalize(). A true
low-latency partial decoder is a deployment-time refinement.
"""

from __future__ import annotations

from secondbrain.voice.ports import Audio, Transcript, TranscriptSegment


class WhisperStreamingStt:
    def __init__(self, model_size: str = "base", *, device: str = "cuda") -> None:
        try:
            from faster_whisper import WhisperModel  # noqa: F401
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("WhisperStreamingStt requires 'faster-whisper': pip install -r requirements-voice.txt") from exc
        from faster_whisper import WhisperModel
        self.model = WhisperModel(model_size, device=device)
        self._buffer = bytearray()

    def push(self, chunk: Audio) -> list[str]:  # pragma: no cover - integration
        self._buffer.extend(chunk.data)
        return []

    def finalize(self) -> Transcript:  # pragma: no cover - integration
        import io
        segments, info = self.model.transcribe(io.BytesIO(bytes(self._buffer)))
        segs = [TranscriptSegment(s.text, s.start, s.end, getattr(s, "avg_logprob", 0.0)) for s in segments]
        self._buffer = bytearray()
        return Transcript.from_segments(segs, language=getattr(info, "language", "en"))
