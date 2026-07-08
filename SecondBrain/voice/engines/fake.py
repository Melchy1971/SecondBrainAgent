"""Deterministic fake voice engines for unit tests (no models)."""

from __future__ import annotations

from secondbrain.voice.ports import Audio, AudioClip, Transcript, TranscriptSegment


class FakeSttEngine:
    name = "fake-stt"

    def __init__(self, text: str = "hello world", confidence: float = 0.9) -> None:
        self._text = text
        self._conf = confidence

    def transcribe(self, audio: Audio, *, lang: str | None = None) -> Transcript:
        segs = [TranscriptSegment(text=part, start=float(i), end=float(i + 1), confidence=self._conf)
                for i, part in enumerate(self._text.split(". ")) if part]
        return Transcript.from_segments(segs, language=lang or "en")


class FakeStreamingStt:
    """Accumulates text from speech chunks encoded as b"S:<text>"."""

    def __init__(self) -> None:
        self._words: list[str] = []

    def push(self, chunk: Audio) -> list[str]:
        data = chunk.data
        if data.startswith(b"S:"):
            self._words.append(data[2:].decode("utf-8", "replace"))
        return [" ".join(self._words)] if self._words else []

    def finalize(self) -> Transcript:
        text = " ".join(self._words)
        return Transcript.from_segments(
            [TranscriptSegment(text, 0.0, float(len(self._words)), 0.9)], language="en")


class FakeVad:
    """Speech iff the chunk is encoded as b"S:..."."""

    def is_speech(self, chunk: Audio) -> bool:
        return chunk.data.startswith(b"S:")


class FakeWakeWord:
    name = "fake-wake"

    def __init__(self, trigger: bytes = b"WAKE") -> None:
        self._trigger = trigger

    def process(self, chunk: Audio) -> bool:
        return chunk.data == self._trigger


class FakeTtsEngine:
    name = "fake-tts"

    def synthesize(self, text: str) -> AudioClip:
        payload = b"RIFF" + text.encode("utf-8")
        return AudioClip(data=payload, sample_rate=22050, format="wav")


class FakeSpeakerEmbedder:
    """Deterministic speaker embedder for tests."""

    name = "fake-embedder"

    def __init__(self, mapping: dict[bytes, list[float]] | None = None) -> None:
        self._mapping = mapping or {}

    def embed(self, audio):
        return self._mapping.get(audio.data, [0.0, 0.0, 1.0])
