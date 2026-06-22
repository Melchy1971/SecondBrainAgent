"""P6 v24.0 - Voice Command Router."""

class VoiceCommandRouter:
    def route(self, text: str) -> str:
        text = (text or "").lower()
        if "mail" in text:
            return "gmail"
        if "kalender" in text:
            return "calendar"
        return "chat"
