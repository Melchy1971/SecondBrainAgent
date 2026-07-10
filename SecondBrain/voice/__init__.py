"""Voice subsystem (v30.83+), offline-first.

The package also preserves the v20 controller exports used by older launcher and
unit-test entry points.
"""

from secondbrain.voice.ports import (
    Audio, AudioClip, TranscriptSegment, Transcript,
    SttEngine, StreamingStt, TtsEngine, MicrophoneSource,
    VoiceActivityDetector, WakeWordDetector, StreamingTts,
)
from secondbrain.voice.transcribe import VoiceTranscriber, transcript_to_item
from secondbrain.voice.speaker import SpeakerId, SpeakerEmbedder, SpeakerProfileStore, SpeakerMatcher, cosine
from secondbrain.voice.memory import VoiceMemory, VoiceMemoryStore
from secondbrain.voice.command_router import VoiceCommandRouter
from secondbrain.voice.commands import Intent
from secondbrain.voice.config import VoiceConfig
from secondbrain.voice.controller import VoiceController
from secondbrain.voice.conversation import ConversationController, State
from secondbrain.voice.dictation import write_dictation
from secondbrain.voice.wake_word_engine import WakeWordEngine
from secondbrain.voice.assistant import (
    ContinuousVoiceAssistant, VoiceConfig as AssistantVoiceConfig, VoiceStatus, MicStatus,
    StreamingTtsPlayer, MissingMicrophoneError, audio_level,
)

__all__ = [
    "Audio", "AudioClip", "TranscriptSegment", "Transcript",
    "SttEngine", "StreamingStt", "TtsEngine", "MicrophoneSource",
    "VoiceActivityDetector", "WakeWordDetector", "StreamingTts",
    "VoiceTranscriber", "transcript_to_item",
    "SpeakerId", "SpeakerEmbedder", "SpeakerProfileStore", "SpeakerMatcher", "cosine",
    "VoiceMemory", "VoiceMemoryStore", "VoiceCommandRouter", "Intent",
    "VoiceConfig", "VoiceController", "WakeWordEngine", "write_dictation",
    "ConversationController", "State",
    "ContinuousVoiceAssistant", "AssistantVoiceConfig", "VoiceStatus", "MicStatus",
    "StreamingTtsPlayer", "MissingMicrophoneError", "audio_level",
]
