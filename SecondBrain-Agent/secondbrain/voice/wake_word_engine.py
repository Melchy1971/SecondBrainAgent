"""P6 v24.0 - Wake Word Engine."""

class WakeWordEngine:
    def __init__(self, wake_word: str = "jarvis"):
        self.wake_word = wake_word.lower()

    def detect(self, text: str) -> bool:
        return self.wake_word in (text or "").lower()
