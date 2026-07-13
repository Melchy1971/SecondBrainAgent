class WakeWordDetector:
    def __init__(self, wake_words: list[str] | None = None):
        self.wake_words = [w.lower() for w in (wake_words or ["jarvis", "secondbrain"])]

    def detect(self, text: str) -> dict:
        lower = text.lower().strip()
        matched = next((w for w in self.wake_words if lower.startswith(w)), None)
        return {
            "detected": matched is not None,
            "wake_word": matched,
            "command_text": lower[len(matched):].strip() if matched else text,
        }
