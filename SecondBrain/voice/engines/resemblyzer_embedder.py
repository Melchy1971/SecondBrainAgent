"""Speaker embedder via Resemblyzer (offline). Lazy dep; integration-only."""

from __future__ import annotations

from secondbrain.voice.ports import Audio


class ResemblyzerEmbedder:
    name = "resemblyzer"

    def __init__(self) -> None:
        try:
            from resemblyzer import VoiceEncoder  # noqa: F401
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("ResemblyzerEmbedder requires 'resemblyzer': pip install resemblyzer") from exc
        from resemblyzer import VoiceEncoder
        self.encoder = VoiceEncoder()

    def embed(self, audio: Audio) -> list[float]:  # pragma: no cover - integration
        import io
        import numpy as np
        from resemblyzer import preprocess_wav
        wav = preprocess_wav(io.BytesIO(audio.data))
        return [float(x) for x in self.encoder.embed_utterance(wav)]
