"""Per-document tags with optional JSON persistence."""

from __future__ import annotations

import json
from pathlib import Path


class TagStore:
    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path else None
        self._tags: dict[str, list[str]] = self._load()

    def _load(self) -> dict[str, list[str]]:
        if self.path and self.path.exists():
            text = self.path.read_text(encoding="utf-8").strip()
            return json.loads(text) if text else {}
        return {}

    def _persist(self) -> None:
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(self._tags, indent=2, sort_keys=True), encoding="utf-8")

    def add(self, doc_id: str, *tags: str) -> list[str]:
        current = set(self._tags.get(doc_id, []))
        current.update(t.strip() for t in tags if t.strip())
        self._tags[doc_id] = sorted(current)
        self._persist()
        return self._tags[doc_id]

    def remove(self, doc_id: str, tag: str) -> list[str]:
        current = [t for t in self._tags.get(doc_id, []) if t != tag]
        self._tags[doc_id] = current
        self._persist()
        return current

    def get(self, doc_id: str) -> list[str]:
        return list(self._tags.get(doc_id, []))

    def all_tags(self) -> list[str]:
        return sorted({t for tags in self._tags.values() for t in tags})

    def find_by_tag(self, tag: str) -> list[str]:
        return sorted([doc for doc, tags in self._tags.items() if tag in tags])
