"""P6 v24.0 - Voice Conversation Manager."""

class VoiceConversationManager:
    def __init__(self):
        self._history = []

    def add(self, role: str, text: str):
        self._history.append({"role": role, "text": text})

    def history(self):
        return list(self._history)
