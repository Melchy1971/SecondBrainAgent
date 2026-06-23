from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .memory import InMemoryMemoryStore, MemoryRecord, MemoryScope, create_memory_record
from .privacy import PrivacyGuard


@dataclass(frozen=True)
class AgentContext:
    workspace_id: str | None = None
    user_text: str = ""
    memories: tuple[MemoryRecord, ...] = ()
    workspace_metadata: dict[str, Any] = field(default_factory=dict)
    request_metadata: dict[str, Any] = field(default_factory=dict)

    def to_prompt_context(self, *, max_memories: int = 8) -> dict[str, Any]:
        memories = self.memories[: max(0, max_memories)]
        return {
            "workspace_id": self.workspace_id,
            "user_text": self.user_text,
            "memories": [memory.text for memory in memories],
            "workspace_metadata": self.workspace_metadata,
            "request_metadata": self.request_metadata,
        }


class ContextBuilder:
    def __init__(self, memory_store: InMemoryMemoryStore | None = None) -> None:
        self.memory_store = memory_store or InMemoryMemoryStore()

    def build(self, *, text: str, workspace_id: str | None = None, metadata: dict[str, Any] | None = None) -> AgentContext:
        memories = tuple(self.memory_store.search(text, workspace_id=workspace_id, limit=8))
        return AgentContext(
            workspace_id=workspace_id,
            user_text=text,
            memories=memories,
            request_metadata=metadata or {},
        )


class MemoryService:
    def __init__(self, store: InMemoryMemoryStore | None = None, privacy_guard: PrivacyGuard | None = None) -> None:
        self.store = store or InMemoryMemoryStore()
        self.privacy_guard = privacy_guard or PrivacyGuard()

    def remember(self, text: str, *, workspace_id: str | None = None, tags: list[str] | None = None) -> MemoryRecord:
        safe_text = self.privacy_guard.require_memory_allowed(text)
        scope = MemoryScope.WORKSPACE if workspace_id else MemoryScope.SESSION
        record = create_memory_record(safe_text, scope=scope, workspace_id=workspace_id, tags=tags)
        return self.store.add(record)

    def recall(self, query: str, *, workspace_id: str | None = None, limit: int = 8) -> list[MemoryRecord]:
        return self.store.search(query, workspace_id=workspace_id, limit=limit)
