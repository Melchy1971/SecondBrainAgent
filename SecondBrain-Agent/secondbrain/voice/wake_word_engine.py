"""Voice Control v20 - Wake Word.

Leichtgewichtig und dependency-frei: Wake-Word-Erkennung auf transkribiertem
Text (Substring + Wortgrenzen-tolerant). Kein Porcupine/API-Key noetig.

Backward-compatible: ``WakeWordEngine.detect(text) -> bool`` bleibt.
"""
from __future__ import annotations

import re


class WakeWordEngine:
    def __init__(self, wake_word: str = "jarvis"):
        self.wake_word = (wake_word or "jarvis").lower().strip()

    def detect(self, text: str) -> bool:
        return self.wake_word in (text or "").lower()

    def strip(self, text: str) -> str:
        """Entfernt das fuehrende Wake-Word inkl. Anrede-Komma/Doppelpunkt."""
        if not text:
            return ""
        pattern = re.compile(rf"^\s*(hey\s+|ok\s+)?{re.escape(self.wake_word)}[\s,:.!-]*",
                             re.IGNORECASE)
        return pattern.sub("", text, count=1).strip()
