"""P5 v23.0 - Chat View Foundation."""

from secondbrain.native.chat import ChatEngine

class ChatView:
    """Presentation adapter backed by the canonical chat engine store."""

    def __init__(self, project_root=".", engine=None):
        self.engine = engine or ChatEngine(project_root)
        self._conversation_id = None

    def add_message(self, role: str, content: str):
        if self._conversation_id is None:
            conversation = self.engine.conversations.create("Chat View", workspace="chat-view")
            self._conversation_id = conversation["id"]
        return self.engine.conversations.append_message(self._conversation_id, role, content)

    def history(self):
        return self.engine.conversations.messages(self._conversation_id) if self._conversation_id else []
