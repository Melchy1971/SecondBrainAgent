"""P6 v24.0 - Speech-to-Text Foundation."""

class SpeechToTextEngine:
    def transcribe(self, chunks: list[str]) -> str:
        return " ".join(chunks).strip()
