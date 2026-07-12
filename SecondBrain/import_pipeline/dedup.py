"""Duplicate Detection über Content-Hashes (SHA-256)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


def content_hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def content_hash_text(text: str) -> str:
    return content_hash_bytes(text.encode("utf-8"))


class DuplicateDetector:
    def __init__(self, project_root: str | Path = "."):
        self.index_path = Path(project_root) / "runtime" / "import_pipeline" / "content_index.json"

    def _load(self) -> dict[str, str]:
        if not self.index_path.exists():
            return {}
        try:
            data = json.loads(self.index_path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except (OSError, json.JSONDecodeError):
            return {}

    def known(self, digest: str) -> str:
        """Returns job_id des Erstimports oder '' wenn unbekannt."""
        return self._load().get(digest, "")

    def register(self, digest: str, job_id: str) -> None:
        index = self._load()
        if digest in index:
            return
        index[digest] = job_id
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.index_path.write_text(
            json.dumps(index, indent=2, sort_keys=True), encoding="utf-8")
