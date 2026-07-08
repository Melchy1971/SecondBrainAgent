"""Voice subsystem (v30.83), offline-first.

Layered like vision so the standard test suite stays green without models/hardware:
- ports:   Audio/Transcript models + Protocols (stdlib-only, unit-testable with fakes)
- engines: STT (faster-whisper) / TTS (Piper) adapters - lazy imports, integration-only
- transcribe: orchestration + Voice-Memory ingest via the existing ConnectorImportBridge
"""

from secondbrain.voice.ports import (
    Audio, AudioClip, TranscriptSegment, Transcript,
    SttEngine, StreamingStt, TtsEngine, MicrophoneSource,
)
from secondbrain.voice.transcribe import VoiceTranscriber, transcript_to_item
from secondbrain.voice.speaker import SpeakerId, SpeakerEmbedder, SpeakerProfileStore, SpeakerMatcher, cosine
from secondbrain.voice.memory import VoiceMemory, VoiceMemoryStore
from secondbrain.voice.commands import VoiceCommandRouter, Intent

__all__ = [
    "Audio", "AudioClip", "TranscriptSegment", "Transcript",
    "SttEngine", "StreamingStt", "TtsEngine", "MicrophoneSource",
    "VoiceTranscriber", "transcript_to_item",
    "SpeakerId", "SpeakerEmbedder", "SpeakerProfileStore", "SpeakerMatcher", "cosine",
    "VoiceMemory", "VoiceMemoryStore", "VoiceCommandRouter", "Intent",
]
