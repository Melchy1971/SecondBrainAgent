"""openWakeWord detector (offline). Lazy dep; integration-only."""

from __future__ import annotations

from secondbrain.voice.ports import Audio


class OpenWakeWordDetector:
    name = "openwakeword"

    def __init__(self, model: str = "hey_jarvis", *, threshold: float = 0.5) -> None:
        try:
            import openwakeword  # noqa: F401
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("OpenWakeWordDetector requires 'openwakeword': pip install -r requirements-voice.txt") from exc
        from openwakeword.model import Model
        self.model = Model(wakeword_models=[model])
        self.threshold = threshold

    def process(self, chunk: Audio) -> bool:  # pragma: no cover - integration
        import numpy as np
        samples = np.frombuffer(chunk.data, dtype=np.int16)
        scores = self.model.predict(samples)
        return any(v >= self.threshold for v in scores.values())
