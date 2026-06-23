"""Saved search support for the desktop search surface.

The module is intentionally storage-agnostic except for the small JSON
repository. It keeps the desktop layer deterministic: saved searches are
validated before persistence, IDs are stable enough for local state, and
queries can be converted back into executable payloads without leaking UI-only
fields into the search pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Iterable
from uuid import uuid4


class SavedSearchError(ValueError):
    """Raised when a saved-search command is invalid."""


@dataclass(slots=True)
class SavedSearch:
    name: str
    query_text: str
    workspace_id: str | None = None
    tags: list[str] = field(default_factory=list)
    status: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    limit: int = 25
    search_id: str = field(default_factory=lambda: f"ss_{uuid4().hex}")
    created_at: str = field(default_factory=lambda: _utc_now())
    updated_at: str = field(default_factory=lambda: _utc_now())
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.name or not self.name.strip():
            raise SavedSearchError("Saved search name is required")
        if len(self.name.strip()) > 120:
            raise SavedSearchError("Saved search name exceeds 120 characters")
        if not self.query_text or not self.query_text.strip():
            raise SavedSearchError("Saved search query_text is required")
        if self.limit < 1 or self.limit > 200:
            raise SavedSearchError("Saved search limit must be between 1 and 200")
        _assert_string_list("tags", self.tags)
        _assert_string_list("status", self.status)
        _assert_string_list("sources", self.sources)

    def normalized(self) -> "SavedSearch":
        self.validate()
        return SavedSearch(
            search_id=self.search_id,
            name=self.name.strip(),
            query_text=" ".join(self.query_text.split()),
            workspace_id=self.workspace_id.strip() if isinstance(self.workspace_id, str) and self.workspace_id.strip() else None,
            tags=_unique_clean(self.tags),
            status=_unique_clean(self.status),
            sources=_unique_clean(self.sources),
            limit=self.limit,
            created_at=self.created_at,
            updated_at=self.updated_at,
            metadata=dict(self.metadata),
        )

    def to_query_payload(self) -> dict[str, Any]:
        saved = self.normalized()
        return {
            "text": saved.query_text,
            "workspace_id": saved.workspace_id,
            "tags": saved.tags,
            "status": saved.status,
            "sources": saved.sources,
            "limit": saved.limit,
            "offset": 0,
        }

    def to_dict(self) -> dict[str, Any]:
        return asdict(self.normalized())

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "SavedSearch":
        return SavedSearch(
            search_id=str(data.get("search_id") or f"ss_{uuid4().hex}"),
            name=str(data.get("name") or ""),
            query_text=str(data.get("query_text") or ""),
            workspace_id=data.get("workspace_id"),
            tags=list(data.get("tags") or []),
            status=list(data.get("status") or []),
            sources=list(data.get("sources") or []),
            limit=int(data.get("limit") or 25),
            created_at=str(data.get("created_at") or _utc_now()),
            updated_at=str(data.get("updated_at") or _utc_now()),
            metadata=dict(data.get("metadata") or {}),
        ).normalized()


class SavedSearchRepository:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def load_all(self) -> list[SavedSearch]:
        if not self.path.exists():
            return []
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(raw, list):
            raise SavedSearchError("Saved search repository must contain a list")
        return [SavedSearch.from_dict(item) for item in raw]

    def save_all(self, searches: Iterable[SavedSearch]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = [search.to_dict() for search in searches]
        self.path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


class SavedSearchService:
    def __init__(self, repository: SavedSearchRepository):
        self.repository = repository
        self._items: dict[str, SavedSearch] = {item.search_id: item for item in repository.load_all()}

    def list(self) -> list[SavedSearch]:
        return sorted(self._items.values(), key=lambda item: item.name.lower())

    def get(self, search_id: str) -> SavedSearch:
        try:
            return self._items[search_id]
        except KeyError as exc:
            raise SavedSearchError(f"Saved search not found: {search_id}") from exc

    def create(self, search: SavedSearch) -> SavedSearch:
        item = search.normalized()
        self._assert_unique_name(item.name)
        self._items[item.search_id] = item
        self._persist()
        return item

    def update(self, search_id: str, **changes: Any) -> SavedSearch:
        current = self.get(search_id)
        data = current.to_dict()
        data.update(changes)
        data["search_id"] = search_id
        data["created_at"] = current.created_at
        data["updated_at"] = _utc_now()
        updated = SavedSearch.from_dict(data)
        self._assert_unique_name(updated.name, ignore_id=search_id)
        self._items[search_id] = updated
        self._persist()
        return updated

    def delete(self, search_id: str) -> SavedSearch:
        removed = self.get(search_id)
        del self._items[search_id]
        self._persist()
        return removed

    def as_query(self, search_id: str) -> dict[str, Any]:
        return self.get(search_id).to_query_payload()

    def _persist(self) -> None:
        self.repository.save_all(self._items.values())

    def _assert_unique_name(self, name: str, ignore_id: str | None = None) -> None:
        candidate = name.strip().lower()
        for item in self._items.values():
            if item.search_id != ignore_id and item.name.strip().lower() == candidate:
                raise SavedSearchError(f"Saved search name already exists: {name}")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _unique_clean(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        cleaned = str(value).strip()
        if cleaned and cleaned.lower() not in seen:
            seen.add(cleaned.lower())
            result.append(cleaned)
    return result


def _assert_string_list(name: str, values: Iterable[Any]) -> None:
    for value in values:
        if not isinstance(value, str):
            raise SavedSearchError(f"{name} must only contain strings")
