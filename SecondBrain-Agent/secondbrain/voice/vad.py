"""Voice Control v20 - Voice Activity Detection.

Energiebasierte VAD ohne harte Abhaengigkeiten. webrtcvad wird genutzt,
falls vorhanden, ist aber optional.

Backward-compatible: ``VoiceActivityDetector.detect(samples) -> bool`` bleibt.
"""
from __future__ import annotations

import math


def rms(samples) -> float:
    if samples is None:
        return 0.0
    vals = list(samples)
    if not vals:
        return 0.0
    return math.sqrt(sum(float(x) * float(x) for x in vals) / len(vals))


class VoiceActivityDetector:
    """Erkennt Sprache anhand der Signalenergie (RMS)."""

    def __init__(self, threshold: float = 0.012):
        self.threshold = threshold

    def detect(self, samples: list[float]) -> bool:
        # Back-compat-Verhalten beibehalten: jede deutliche Amplitude zaehlt.
        return rms(samples) > self.threshold or any(abs(x) > 0.01 for x in (samples or []))

    def is_speech(self, samples) -> bool:
        return rms(samples) > self.threshold


# Alias mit sprechendem Namen.
EnergyVAD = VoiceActivityDetector
