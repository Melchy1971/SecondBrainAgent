"""Voice transcription orchestration + Voice-Memory ingest into Memory/RAG."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from typing import Any

from secondbrain.connectors.adapter_contract import ConnectorItem
from secondbrain.connectors.import_bridge import ConnectorImportBridge, ImportJobSink, InMemoryImportJobSink
from secondbrain.voice.ports import Audio, Transcript, SttEngine

SOURCE = "voice_stt"


def transcript_to_item(transcript: Transcript, *, source_uri: str, title: str | None = None) -> ConnectorItem:
    content = transcript.text
    ext = sha256(f"{source_uri}\n{content}".encode("utf-8")).hexdigest()
    first = content.split(".")[0][:80] if content else ""
    return ConnectorItem(
        external_id=ext, source=SOURCE,
        title=title or (first if first else "(voice note)"),
        content=content or "(empty transcript)",
        updated_at=datetime.now(timezone.utc), uri=source_uri,
        metadata={"language": transcript.language, "segments": len(transcript.segments),
                  "mean_confidence": round(transcript.mean_confidence, 2)},
    )


class VoiceTranscriber:
    def __init__(self, stt: SttEngine, *, sink: ImportJobSink | None = None) -> None:
        self.stt = stt
        self.sink = sink or InMemoryImportJobSink()

    def transcribe(self, audio: Audio, *, lang: str | None = None, source_uri: str | None = None) -> dict[str, Any]:
        uri = source_uri or audio.source_uri or "audio://inline"
        transcript = self.stt.transcribe(audio, lang=lang)
        item = transcript_to_item(transcript, source_uri=uri)
        bridge = ConnectorImportBridge(sink=self.sink)
        bridge.process_item(item)
        return {
            "source_uri": uri,
            "transcript": {"text": transcript.text, "language": transcript.language,
                           "segments": len(transcript.segments),
                           "mean_confidence": round(transcript.mean_confidence, 2)},
            "item": item.external_id,
            "import": bridge.snapshot(),
        }

    def transcribe_path(self, path: str, *, lang: str | None = None) -> dict[str, Any]:
        return self.transcribe(Audio.from_path(path), lang=lang)
