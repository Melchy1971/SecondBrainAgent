"""WebRTC VAD adapter (offline). Lazy dep; integration-only."""

from __future__ import annotations

from secondbrain.voice.ports import Audio


class WebRtcVad:
    def __init__(self, aggressiveness: int = 2, *, sample_rate: int = 16000) -> None:
        try:
            import webrtcvad  # noqa: F401
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("WebRtcVad requires 'webrtcvad': pip install -r requirements-voice.txt") from exc
        import webrtcvad
        self._vad = webrtcvad.Vad(aggressiveness)
        self.sample_rate = sample_rate

    def is_speech(self, chunk: Audio) -> bool:  # pragma: no cover - integration
        return self._vad.is_speech(chunk.data, self.sample_rate)
