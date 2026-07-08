"""v30.64 Agent Memory Injection - service facade for the launcher CLI.

Loads memory records into the canonical ``InMemoryMemoryStore`` and runs the
injector against them. Records are read from a JSON export so the CLI has data
to work with without standing up the full memory runtime.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from secondbrain.agent.memory import (
    MemoryScope,
    MemoryVisibility,
    InMemoryMemoryStore,
    create_memory_record,
)

from .injector import MemoryInjector
from .models import MemoryQuery


def _load_store_from_json(path: str | Path) -> InMemoryMemoryStore:
    store = InMemoryMemoryStore()
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    items = data.get("records", data) if isinstance(data, dict) else data
    for item in items:
        try:
            record = create_memory_record(
                item["text"],
                scope=MemoryScope(item.get("scope", "session")),
                visibility=MemoryVisibility(item.get("visibility", "private")),
                workspace_id=item.get("workspace_id"),
                tags=item.get("tags") or (),
                metadata=item.get("metadata") or {},
            )
            store.add(record)
        except Exception:
            # skip malformed/duplicate rows; the injector operates on what loaded
            continue
    return store


class MemoryInjectionService:
    def __init__(self, project_root: str | Path, *, store: InMemoryMemoryStore | None = None):
        self.project_root = Path(project_root).resolve()
        self.store = store or InMemoryMemoryStore()
        self.injector = MemoryInjector.for_project(self.project_root, self.store)

    def load_memories(self, path: str | Path) -> int:
        self.store = _load_store_from_json(path)
        self.injector = MemoryInjector.for_project(self.project_root, self.store)
        return len(self.store.list())

    def _query(self, args: dict[str, Any]) -> MemoryQuery:
        tags = args.get("tags")
        return MemoryQuery(
            text=args.get("text", ""),
            workspace_id=args.get("workspace_id"),
            limit=int(args.get("limit", 10)),
            privacy_mode=bool(args.get("privacy_mode", False)),
            token_budget=args.get("token_budget"),
            tags=tuple(tags.split(",")) if isinstance(tags, str) and tags else (),
            require_source=bool(args.get("require_source", False)),
            min_relevance=float(args.get("min_relevance", 0.0)),
        )

    def preview(self, args: dict[str, Any]) -> dict[str, Any]:
        context = self.injector.preview(self._query(args))
        return {"ok": True, **context.to_dict()}

    def inject(self, args: dict[str, Any], *, actor: str = "agent", agent_id: str = "") -> dict[str, Any]:
        context = self.injector.inject(self._query(args), actor=actor, agent_id=agent_id)
        return {"ok": True, **context.to_dict()}

    def audit(self, agent_id: str | None = None, *, limit: int = 100) -> dict[str, Any]:
        events = self.injector.audit.events(agent_id, limit=limit) if self.injector.audit else []
        return {"ok": True, "count": len(events), "events": events}
