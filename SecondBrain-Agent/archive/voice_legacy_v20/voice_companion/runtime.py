from .store import VoiceStore
from .wake_word import WakeWordDetector
from .streaming import StreamingSTTAdapter, StreamingTTSAdapter
from .memory import VoiceMemory
from .commands import VoiceCommandRouter
from .conversation import RealtimeConversation


class VoiceCompanion:
    def __init__(self, root="."):
        self.store = VoiceStore(root)
        self.wake = WakeWordDetector()
        self.stt = StreamingSTTAdapter()
        self.tts = StreamingTTSAdapter()
        self.memory = VoiceMemory(self.store)
        self.router = VoiceCommandRouter()
        self.conversation = RealtimeConversation(self.store, self.memory, self.router, self.tts)

    def status(self) -> dict:
        return {
            "version": "13.5",
            "wake_words": self.wake.wake_words,
            "sessions": len(self.conversation.sessions()),
            "turns": len(self.conversation.turns()),
            "memory_items": len(self.memory.all()),
            "stt": "manual_stream_stt",
            "tts": "console_stream_tts",
        }

    def wake_and_handle(self, text: str) -> dict:
        wake = self.wake.detect(text)
        if not wake["detected"]:
            return {"ok": False, "reason": "wake_word_not_detected", "wake": wake}
        return {"ok": True, "wake": wake, "turn": self.conversation.handle_text(wake["command_text"])}
