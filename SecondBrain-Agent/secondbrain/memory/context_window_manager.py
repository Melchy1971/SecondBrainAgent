"""P3 v20.2 - Context Window Management."""

class ContextWindowManager:
    def trim(self, texts: list[str], max_chars: int = 4000) -> list[str]:
        result = []
        size = 0
        for text in texts:
            length = len(text)
            if size + length > max_chars:
                break
            result.append(text)
            size += length
        return result
