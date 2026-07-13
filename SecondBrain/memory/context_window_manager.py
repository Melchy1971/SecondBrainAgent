"""P3 v20.2 / v30.46.2 - Kompatibilitaets-Shim.

Die Implementierung lebt in secondbrain.chat.context.limiter.ContextLimiter.
Der bisherige Kontrakt (trim(texts, max_chars) -> list[str]) bleibt.
"""
from secondbrain.chat.context.limiter import ContextLimiter


class ContextWindowManager:
    def trim(self, texts: list[str], max_chars: int = 4000) -> list[str]:
        return ContextLimiter().trim_items(texts, max_chars=max_chars)
