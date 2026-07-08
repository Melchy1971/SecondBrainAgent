"""Document versioning: content-hashed, ordered versions with diffable content."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256


@dataclass(frozen=True)
class DocumentVersion:
    doc_id: str
    version: int
    content_hash: str
    created_at: str
    size: int
    note: str = ""


class VersionStore:
    def __init__(self) -> None:
        self._versions: dict[str, list[tuple[DocumentVersion, str]]] = {}

    def add_version(self, doc_id: str, content: str, *, note: str = "") -> DocumentVersion:
        history = self._versions.setdefault(doc_id, [])
        digest = sha256(content.encode("utf-8")).hexdigest()
        if history and history[-1][0].content_hash == digest:
            return history[-1][0]                      # unchanged -> no new version
        version = DocumentVersion(doc_id=doc_id, version=len(history) + 1, content_hash=digest,
                                  created_at=datetime.now(timezone.utc).isoformat(),
                                  size=len(content), note=note)
        history.append((version, content))
        return version

    def list(self, doc_id: str) -> list[DocumentVersion]:
        return [v for v, _ in self._versions.get(doc_id, [])]

    def content(self, doc_id: str, version: int) -> str:
        for v, c in self._versions.get(doc_id, []):
            if v.version == version:
                return c
        raise KeyError(f"no version {version} for {doc_id}")

    def latest(self, doc_id: str) -> DocumentVersion | None:
        history = self._versions.get(doc_id, [])
        return history[-1][0] if history else None
