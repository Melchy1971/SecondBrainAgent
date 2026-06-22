"""P7 v25.0 - Mobile Chat UI."""

class MobileChatUi:
    def render(self, messages: list[dict]):
        return {
            "messages": len(messages),
            "items": messages,
        }
