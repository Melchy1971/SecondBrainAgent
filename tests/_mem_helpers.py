"""Shared helpers for v30.64 memory-injection tests."""

from __future__ import annotations

from secondbrain.agent.memory import (
    InMemoryMemoryStore,
    MemoryScope,
    MemoryVisibility,
    create_memory_record,
)


def make_record(text, *, source="src", scope="session", visibility="public",
                workspace_id=None, tags=(), metadata=None):
    md = dict(metadata or {})
    if source is not None and "source" not in md:
        md["source"] = source
    return create_memory_record(
        text,
        scope=MemoryScope(scope),
        visibility=MemoryVisibility(visibility),
        workspace_id=workspace_id,
        tags=tuple(tags),
        metadata=md,
    )


def make_store(records):
    store = InMemoryMemoryStore()
    for rec in records:
        store.add(rec)
    return store
