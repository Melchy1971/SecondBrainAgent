"""Voice ports: stdlib-only audio/transcript models and Protocols."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class Audio:
    data: bytes
    sample_rate: int = 16000
    channels: int = 1
    format: str = "wav"
    source_uri: str | None = None

    @classmethod
    def from_path(cls, path: str | Path, *, sample_rate: int = 16000) -> "Audio":
        p = Path(path)
        return cls(data=p.read_bytes(), sample_rate=sample_rate,
                   format=p.suffix.lstrip(".").lower() or "wav", source_uri=p.as_uri())


@dataclass(frozen=True)
class AudioClip:
    data: bytes
    sample_rate: int = 22050
    format: str = "wav"

    def write(self, path: str | Path) -> str:
        p = Path(path)
        p.write_bytes(self.data)
        return str(p)


@dataclass(frozen=True)
class TranscriptSegment:
    text: str
    start: float
    end: float
    confidence: float = 0.0


@dataclass(frozen=True)
class Transcript:
    text: str
    segments: list[TranscriptSegment] = field(default_factory=list)
    language: str = "en"
    mean_confidence: float = 0.0

    @classmethod
    def from_segments(cls, segments: list[TranscriptSegment], *, language: str = "en") -> "Transcript":
        text = " ".join(s.text.strip() for s in segments if s.text.strip())
        conf = sum(s.confidence for s in segments) / len(segments) if segments else 0.0
        return cls(text=text, segments=list(segments), language=language, mean_confidence=conf)


@runtime_checkable
class SttEngine(Protocol):
    name: str
    def transcribe(self, audio: Audio, *, lang: str | None = None) -> Transcript: ...


@runtime_checkable
class StreamingStt(Protocol):
    """Chunked STT (used by v30.84 streaming/conversation)."""
    def push(self, chunk: Audio) -> list[str]: ...
    def finalize(self) -> Transcript: ...


@runtime_checkable
class TtsEngine(Protocol):
    name: str
    def synthesize(self, text: str) -> AudioClip: ...


@runtime_checkable
class MicrophoneSource(Protocol):
    def record(self, seconds: float) -> Audio: ...


@runtime_checkable
class VoiceActivityDetector(Protocol):
    def is_speech(self, chunk: Audio) -> bool: ...


@runtime_checkable
class WakeWordDetector(Protocol):
    name: str
    def process(self, chunk: Audio) -> bool: ...


@runtime_checkable
class StreamingTts(Protocol):
    def stream(self, text: str): ...  # -> Iterator[AudioClip]
