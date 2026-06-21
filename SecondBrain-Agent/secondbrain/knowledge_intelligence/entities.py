import re
from uuid import uuid4


class EntityExtractor:
    def extract(self, text: str) -> list[dict]:
        candidates = set(re.findall(r"\b[A-ZÄÖÜ][A-Za-zÄÖÜäöüß0-9_-]{2,}\b", text))
        return [
            {"id": str(uuid4()), "name": name, "kind": self._kind(name), "confidence": 0.6}
            for name in sorted(candidates)
        ]

    def _kind(self, name: str) -> str:
        lower = name.lower()
        if lower in {"gmail", "github", "paperless", "obsidian", "neo4j"}:
            return "system"
        if lower.startswith("v") and any(ch.isdigit() for ch in lower):
            return "version"
        return "concept"


class EntityResolver:
    def __init__(self, store):
        self.store = store

    def resolve(self, entities: list[dict]) -> list[dict]:
        known = self.store.load("entities", [])
        by_norm = {e["name"].lower(): e for e in known}
        resolved = []
        changed = False
        for entity in entities:
            key = entity["name"].lower()
            if key in by_norm:
                resolved.append({**by_norm[key], "mentions": by_norm[key].get("mentions", 1) + 1})
            else:
                entity = {**entity, "mentions": 1}
                known.append(entity)
                by_norm[key] = entity
                resolved.append(entity)
                changed = True
        if changed:
            self.store.save("entities", known)
        return resolved

    def entities(self) -> list[dict]:
        return self.store.load("entities", [])
