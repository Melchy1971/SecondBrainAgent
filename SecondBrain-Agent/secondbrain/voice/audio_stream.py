"""Voice Control v20 - Mikrofon-Aufnahme.

MicrophoneStream nimmt ueber sounddevice auf und beendet bei Stille
(Energie-VAD). Optionale Abhaengigkeit: bei fehlendem sounddevice/numpy wird
ein klarer Fehler geworfen, der Import des Moduls bleibt moeglich.

Backward-compatible: die alte ``AudioStream``-Pufferklasse bleibt erhalten.
"""
from __future__ import annotations

import time

from .vad import rms

try:
    import numpy as np  # type: ignore
except Exception:  # pragma: no cover
    np = None  # type: ignore


class AudioUnavailable(RuntimeError):
    """Mikrofon-/Audio-Stack nicht verfuegbar."""


class AudioStream:
    """Einfacher Frame-Puffer (Back-compat)."""

    def __init__(self):
        self._frames = []

    def push(self, frame):
        self._frames.append(frame)

    def size(self):
        return len(self._frames)


class MicrophoneStream:
    """Aufnahme einer einzelnen Aeusserung bis zur Stille."""

    def __init__(self, sample_rate: int = 16000, silence_threshold: float = 0.012,
                 silence_duration: float = 1.0, max_seconds: float = 20.0):
        self.sample_rate = sample_rate
        self.silence_threshold = silence_threshold
        self.silence_duration = silence_duration
        self.max_seconds = max_seconds

    @staticmethod
    def available() -> bool:
        try:
            import sounddevice  # noqa: F401
            return np is not None
        except Exception:
            return False

    def record_utterance(self):
        """Nimmt auf, bis ``silence_duration`` Sek. Stille erkannt werden.

        Rueckgabe: float32-Numpy-Array (mono).
        """
        if not self.available():
            raise AudioUnavailable(
                "sounddevice/numpy fehlen. pip install -r requirements-voice.txt"
            )
        import sounddevice as sd  # type: ignore

        block = int(self.sample_rate * 0.1)  # 100ms-Bloecke
        collected = []
        silent_for = 0.0
        spoke = False
        started = time.time()
        with sd.InputStream(samplerate=self.sample_rate, channels=1,
                            dtype="float32", blocksize=block) as stream:
            while True:
                data, _ = stream.read(block)
                mono = data[:, 0]
                collected.append(mono.copy())
                level = rms(mono.tolist())
                if level > self.silence_threshold:
                    spoke = True
                    silent_for = 0.0
                else:
                    silent_for += 0.1
                if spoke and silent_for >= self.silence_duration:
                    break
                if time.time() - started > self.max_seconds:
                    break
        if not collected:
            return np.zeros(0, dtype="float32")
        return np.concatenate(collected)
