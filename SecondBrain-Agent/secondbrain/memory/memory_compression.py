"""P3 v20.1 - Memory Compression."""

class MemoryCompressor:
    def compress(self, text: str, max_chars: int = 500) -> str:
        text = " ".join((text or "").split())
        return text[:max_chars]
