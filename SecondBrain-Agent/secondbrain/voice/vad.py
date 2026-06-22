"""P6 v24.1 - Voice Activity Detection."""

class VoiceActivityDetector:
    def detect(self, samples: list[float]) -> bool:
        return any(abs(x) > 0.01 for x in samples)
