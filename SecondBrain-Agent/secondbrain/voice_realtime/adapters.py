from __future__ import annotations
from typing import Iterable

class ManualStreamingSTT:
    """Offline-safe STT adapter. Accepts provided text chunks and emits final text."""
    name = 'manual_streaming_stt'
    def transcribe_chunks(self, chunks: Iterable[str]) -> str:
        return ' '.join(c.strip() for c in chunks if c and c.strip()).strip()

class ConsoleStreamingTTS:
    """Offline-safe TTS adapter. Stores/returns speech events instead of using audio devices."""
    name = 'console_streaming_tts'
    def speak(self, text: str) -> dict:
        return {'adapter': self.name, 'spoken': text, 'chars': len(text)}

class WakeWordDetector:
    def __init__(self, wake_words: list[str] | None = None):
        self.wake_words = [w.lower() for w in (wake_words or ['jarvis', 'second brain'])]
    def detect(self, text: str) -> dict:
        low = (text or '').lower()
        hits = [w for w in self.wake_words if w in low]
        return {'detected': bool(hits), 'wake_words': hits}
