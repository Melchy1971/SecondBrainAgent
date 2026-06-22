"""P5 v23.2 - Chat Streaming."""

class ChatStream:
    def __init__(self):
        self._chunks = []

    def push(self, chunk: str):
        self._chunks.append(chunk)

    def content(self) -> str:
        return "".join(self._chunks)
