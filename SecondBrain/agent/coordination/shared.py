"""v30.69 Multi-Agent Coordination - shared state.

Three shared surfaces the specialists collaborate through, each backed by an
existing subsystem (no new storage engine):

* SharedContext - an in-session blackboard (key/value + history).
* SharedMemory  - the existing ``secondbrain.agent.memory`` store; recall via the
  v30.64 ``MemoryInjector``.
* SharedGoals   - the v30.65 ``GoalTracker``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


class SharedContext:
    def __init__(self) -> None:
        self._data: dict[str, Any] = {}
        self.history: list[dict[str, Any]] = []

    def set(self, key: str, value: Any, *, by: str = "coordinator") -> None:
        self._data[key] = value
        self.history.append({"key": key, "by": by})

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def keys(self) -> list[str]:
        return list(self._data.keys())

    def to_dict(self) -> dict[str, Any]:
        return dict(self._data)


class SharedMemory:
    def __init__(self, store: Any | None = None, *, project_root: str | Path | None = None):
        if store is None:
            from secondbrain.agent.memory import InMemoryMemoryStore
            store = InMemoryMemoryStore()
        self.store = store
        self.project_root = Path(project_root).resolve() if project_root else None

    def remember(self, text: str, *, source: str = "agent", scope: str = "workspace",
                 workspace_id: str | None = None, tags=(), metadata: dict | None = None) -> Any:
        from secondbrain.agent.memory import MemoryScope, MemoryVisibility, create_memory_record
        md = dict(metadata or {})
        md.setdefault("source", source)
        record = create_memory_record(
            text, scope=MemoryScope(scope), visibility=MemoryVisibility.WORKSPACE,
            workspace_id=workspace_id or "shared", tags=tuple(tags), metadata=md,
        )
        try:
            return self.store.add(record)
        except Exception:
            return record

    def recall(self, query: str, *, limit: int = 10, privacy_mode: bool = False) -> list[dict[str, Any]]:
        from secondbrain.agent.memory_injection import MemoryInjector, MemoryQuery
        ctx = MemoryInjector(self.store).preview(
            MemoryQuery(text=query, limit=limit, privacy_mode=privacy_mode, require_source=False))
        return [e.to_dict() for e in ctx.evidences]


class SharedGoals:
    def __init__(self, tracker: Any | None = None, *, project_root: str | Path | None = None):
        if tracker is None:
            if project_root is None:
                raise ValueError("project_root or tracker required")
            from secondbrain.agent.goals import GoalTracker
            tracker = GoalTracker.for_project(project_root)
        self.tracker = tracker

    def create(self, title: str, **kwargs) -> Any:
        return self.tracker.create_goal(title, **kwargs)

    def list(self) -> list[dict[str, Any]]:
        return self.tracker.list()

    def progress(self, goal_id: str) -> dict[str, Any]:
        return self.tracker.measure_progress(goal_id).to_dict()

    def report(self, goal_id: str) -> dict[str, Any]:
        return self.tracker.report(goal_id)
