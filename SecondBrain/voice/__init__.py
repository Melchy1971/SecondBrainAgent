"""Voice subsystem (v30.83+), offline-first.

Layered like vision so the standard test suite stays green without models/hardware:
- ports:   Audio/Transcript models + Protocols (stdlib-only, unit-testable with fakes)
- engines: STT (faster-whisper) / TTS (Piper) / VAD / wake-word adapters - lazy, integration-only
- conversation/assistant: continuous full-duplex assistant with barge-in (deterministic)
"""

from secondbrain.voice.ports import (
    Audio, AudioClip, TranscriptSegment, Transcript,
    SttEngine, StreamingStt, TtsEngine, MicrophoneSource,
    VoiceActivityDetector, WakeWordDetector, StreamingTts,
)
from secondbrain.voice.transcribe import VoiceTranscriber, transcript_to_item
from secondbrain.voice.speaker import SpeakerId, SpeakerEmbedder, SpeakerProfileStore, SpeakerMatcher, cosine
from secondbrain.voice.memory import VoiceMemory, VoiceMemoryStore
from secondbrain.voice.commands import VoiceCommandRouter, Intent
from secondbrain.voice.conversation import ConversationController, State
from secondbrain.voice.assistant import (
    ContinuousVoiceAssistant, VoiceConfig, VoiceStatus, MicStatus,
    StreamingTtsPlayer, MissingMicrophoneError, audio_level,
)

__all__ = [
    "Audio", "AudioClip", "TranscriptSegment", "Transcript",
    "SttEngine", "StreamingStt", "TtsEngine", "MicrophoneSource",
    "VoiceActivityDetector", "WakeWordDetector", "StreamingTts",
    "VoiceTranscriber", "transcript_to_item",
    "SpeakerId", "SpeakerEmbedder", "SpeakerProfileStore", "SpeakerMatcher", "cosine",
    "VoiceMemory", "VoiceMemoryStore", "VoiceCommandRouter", "Intent",
    "ConversationController", "State",
    "ContinuousVoiceAssistant", "VoiceConfig", "VoiceStatus", "MicStatus",
    "StreamingTtsPlayer", "MissingMicrophoneError", "audio_level",
]
