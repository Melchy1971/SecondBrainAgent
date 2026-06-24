"""Voice Control v20 - konsolidierte Sprachsteuerung fuer Jarvis.

Einheitlicher Einstieg. Ersetzt die verstreuten Stub-Module
(voice_assistant_v9, voice_layer_v103, voice_runtime_v114, voice_realtime,
voice_companion, realtime_voice). Hardware-Provider sind optional und werden
lazy importiert.
"""
from .config import VoiceConfig
from .command_router import Intent, VoiceCommandRouter
from .controller import Response, VoiceController
from .dictation import write_dictation
from .hud_bridge import HudBridge
from .wake_word_engine import WakeWordEngine

__all__ = [
    "VoiceConfig", "VoiceController", "Response", "VoiceCommandRouter",
    "Intent", "HudBridge", "WakeWordEngine", "write_dictation",
]
