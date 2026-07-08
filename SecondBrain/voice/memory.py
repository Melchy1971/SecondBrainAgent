"""Persistent voice memory: speaker-attributed transcripts + RAG ingest."""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any

from secondbrain.connectors.import_bridge import ConnectorImportBridge, ImportJobSink, InMemoryImportJobSink
from secondbrain.voice.ports import Audio, Transcript
from secondbrain.voice.transcribe import transcript_to_item
from secondbrain.voice.speaker import SpeakerMatcher, SpeakerId


class VoiceMemoryStore:
    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path else None
        self._lock = RLock()
        self._records: list[dict] = self._load()

    def _load(self) -> list[dict]:
        if self.path and self.path.exists():
            text = self.path.read_text(encoding="utf-8").strip()
            return json.loads(text) if text else []
        return []

    def append(self, record: dict) -> None:
        with self._lock:
            self._records.append(record)
            if self.path:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                tmp = self.path.with_suffix(self.path.suffix + ".tmp")
                tmp.write_text(json.dumps(self._records, indent=2), encoding="utf-8")
                tmp.replace(self.path)

    def all(self) -> list[dict]:
        return list(self._records)


class VoiceMemory:
    """Records a transcript with optional speaker attribution and ingests to RAG."""

    def __init__(self, store: VoiceMemoryStore, *, sink: ImportJobSink | None = None,
                 matcher: SpeakerMatcher | None = None) -> None:
        self.store = store
        self.sink = sink or InMemoryImportJobSink()
        self.matcher = matcher

    def remember(self, transcript: Transcript, *, audio: Audio | None = None,
                 source_uri: str = "audio://voice") -> dict[str, Any]:
        speaker: SpeakerId | None = None
        if self.matcher is not None and audio is not None:
            speaker = self.matcher.identify(audio)
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "speaker": speaker.id if speaker else None,
            "speaker_label": speaker.label if speaker else None,
            "text": transcript.text,
            "source_uri": source_uri,
        }
        self.store.append(record)
        item = transcript_to_item(transcript, source_uri=source_uri)
        if speaker:
            item = replace(item, metadata={**item.metadata, "speaker": speaker.id,
                                           "speaker_label": speaker.label})
        bridge = ConnectorImportBridge(sink=self.sink)
        bridge.process_item(item)
        return {"record": record, "import": bridge.snapshot()}
