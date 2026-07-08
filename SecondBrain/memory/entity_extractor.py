"""P3 v20.3 - Lightweight Entity Extraction."""

import re


class EntityExtractor:
    def extract(self, text: str) -> list[str]:
        candidates = re.findall(r"\b[A-ZÄÖÜ][A-Za-zÄÖÜäöüß0-9_-]{2,}\b", text or "")
        return sorted(set(candidates))
