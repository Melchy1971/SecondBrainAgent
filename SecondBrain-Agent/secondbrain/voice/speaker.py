"""Speaker profiles: enrollment + identification via embedding cosine similarity.

The matcher/store/cosine logic is pure Python (no numpy) -> unit-testable green.
Real voice embedders (resemblyzer/pyannote) implement the SpeakerEmbedder port.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from typing import Protocol, runtime_checkable

from secondbrain.voice.ports import Audio


@dataclass(frozen=True)
class SpeakerId:
    id: str
    label: str
    score: float


@runtime_checkable
class SpeakerEmbedder(Protocol):
    name: str
    def embed(self, audio: Audio) -> list[float]: ...


def cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def _mean(vectors: list[list[float]]) -> list[float]:
    if not vectors:
        return []
    n = len(vectors)
    dim = len(vectors[0])
    return [sum(v[i] for v in vectors) / n for i in range(dim)]


class SpeakerProfileStore:
    """Durable {speaker_id: {label, embedding}} store."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path else None
        self._lock = RLock()
        self._profiles: dict[str, dict] = self._load()

    def _load(self) -> dict[str, dict]:
        if self.path and self.path.exists():
            text = self.path.read_text(encoding="utf-8").strip()
            return json.loads(text) if text else {}
        return {}

    def _persist(self) -> None:
        if not self.path:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(self._profiles, indent=2), encoding="utf-8")
        tmp.replace(self.path)

    def put(self, speaker_id: str, label: str, embedding: list[float]) -> None:
        with self._lock:
            self._profiles[speaker_id] = {"label": label, "embedding": embedding}
            self._persist()

    def get(self, speaker_id: str) -> dict | None:
        return self._profiles.get(speaker_id)

    def all(self) -> dict[str, dict]:
        return dict(self._profiles)

    def delete(self, speaker_id: str) -> bool:
        with self._lock:
            existed = speaker_id in self._profiles
            self._profiles.pop(speaker_id, None)
            if existed:
                self._persist()
            return existed


class SpeakerMatcher:
    def __init__(self, embedder: SpeakerEmbedder, store: SpeakerProfileStore, *, threshold: float = 0.75) -> None:
        self.embedder = embedder
        self.store = store
        self.threshold = threshold

    def enroll(self, speaker_id: str, label: str, audios: list[Audio]) -> list[float]:
        embedding = _mean([self.embedder.embed(a) for a in audios])
        self.store.put(speaker_id, label, embedding)
        return embedding

    def identify(self, audio: Audio) -> SpeakerId:
        vec = self.embedder.embed(audio)
        best_id, best_label, best_score = "unknown", "unknown", 0.0
        for sid, prof in self.store.all().items():
            score = cosine(vec, prof.get("embedding", []))
            if score > best_score:
                best_id, best_label, best_score = sid, prof.get("label", sid), score
        if best_score >= self.threshold:
            return SpeakerId(best_id, best_label, round(best_score, 4))
        return SpeakerId("unknown", "unknown", round(best_score, 4))
