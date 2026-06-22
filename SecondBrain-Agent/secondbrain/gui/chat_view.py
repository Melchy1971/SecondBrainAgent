"""P5 v23.0 - Chat View Foundation."""

class ChatView:
    def __init__(self):
        self.messages = []

    def add_message(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})

    def history(self):
        return list(self.messages)
