"""P6 v24.0 - Text-to-Speech Foundation."""

class TextToSpeechEngine:
    def synthesize(self, text: str) -> bytes:
        return text.encode("utf-8")
