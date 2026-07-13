"""P6 v24.0 - Voice Conversation Manager."""

from secondbrain.native.chat import ChatEngine

class VoiceConversationManager:
    """Voice adapter using the same conversation store as every chat surface."""

    def __init__(self, project_root=".", engine=None):
        self.engine = engine or ChatEngine(project_root)
        self._conversation_id = None

    def add(self, role: str, text: str):
        if self._conversation_id is None:
            conversation = self.engine.conversations.create("Voice Conversation", workspace="voice")
            self._conversation_id = conversation["id"]
        return self.engine.conversations.append_message(self._conversation_id, role, text, metadata={"source": "voice"})

    def history(self):
        if self._conversation_id is None:
            return []
        return [{"role": row["role"], "text": row["content"]} for row in self.engine.conversations.messages(self._conversation_id)]
