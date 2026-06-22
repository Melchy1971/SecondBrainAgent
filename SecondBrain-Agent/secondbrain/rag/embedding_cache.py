"""P1 v19.3 - deterministic embedding cache.

Cache key = provider + model + sha256(normalized text).
The cache is intentionally file-system based so it works before the
PostgreSQL/pgvector stack is available.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from time import time
from typing import Iterable


def normalize_text(text: str) -> str:
    return " ".join((text or "").strip().split())


def embedding_cache_key(text: str, *, provider: str, model: str) -> str:
    payload = f"{provider}:{model}:{normalize_text(text)}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class CachedEmbedding:
    key: str
    provider: str
    model: str
    vector: list[float]
    created_at: float


class EmbeddingCache:
    def __init__(self, path: str | Path = "runtime/rag/embedding_cache.jsonl") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _load_all(self) -> dict[str, CachedEmbedding]:
        if not self.path.exists():
            return {}
        result: dict[str, CachedEmbedding] = {}
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            result[row["key"]] = CachedEmbedding(
                key=row["key"],
                provider=row["provider"],
                model=row["model"],
                vector=[float(x) for x in row["vector"]],
                created_at=float(row["created_at"]),
            )
        return result

    def get(self, text: str, *, provider: str, model: str) -> list[float] | None:
        key = embedding_cache_key(text, provider=provider, model=model)
        item = self._load_all().get(key)
        return None if item is None else item.vector

    def put(self, text: str, vector: Iterable[float], *, provider: str, model: str) -> str:
        key = embedding_cache_key(text, provider=provider, model=model)
        rows = self._load_all()
        rows[key] = CachedEmbedding(
            key=key,
            provider=provider,
            model=model,
            vector=[float(x) for x in vector],
            created_at=time(),
        )
        self._rewrite(rows)
        return key

    def invalidate_text(self, text: str, *, provider: str, model: str) -> bool:
        key = embedding_cache_key(text, provider=provider, model=model)
        rows = self._load_all()
        existed = key in rows
        rows.pop(key, None)
        self._rewrite(rows)
        return existed

    def stats(self) -> dict[str, int]:
        rows = self._load_all()
        providers = {f"{r.provider}:{r.model}" for r in rows.values()}
        return {"entries": len(rows), "provider_models": len(providers)}

    def _rewrite(self, rows: dict[str, CachedEmbedding]) -> None:
        lines = [
            json.dumps({
                "key": item.key,
                "provider": item.provider,
                "model": item.model,
                "vector": item.vector,
                "created_at": item.created_at,
            }, ensure_ascii=False, sort_keys=True)
            for item in rows.values()
        ]
        self.path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
