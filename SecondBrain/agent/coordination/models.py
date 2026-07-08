"""v30.69 Multi-Agent Coordination - value objects.

Coordinates the *existing* agents (Planner, Workflow Executor, Memory, Goals,
Reasoning, Background monitors) - no second agent engine. These are the
messages passed between them.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:10]}"


# Task kinds (capabilities). Each specialist declares the kinds it handles.
KIND_PLAN = "plan"
KIND_EXECUTE = "execute"
KIND_REVIEW = "review"
KIND_CRITIQUE = "critique"
KIND_MEMORY_STORE = "memory.store"
KIND_MEMORY_RECALL = "memory.recall"
KIND_IMPORT_CHECK = "import.check"
KIND_SEARCH = "search"


@dataclass
class AgentTask:
    id: str
    kind: str
    payload: dict[str, Any] = field(default_factory=dict)
    requester: str = "coordinator"
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def create(cls, kind: str, payload: dict | None = None, *, requester: str = "coordinator") -> "AgentTask":
        return cls(id=new_id("task"), kind=kind, payload=payload or {}, requester=requester)


@dataclass
class AgentResult:
    task_id: str
    agent: str
    ok: bool
    output: Any = None
    error: str = ""
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def success(cls, task_id: str, agent: str, output: Any) -> "AgentResult":
        return cls(task_id=task_id, agent=agent, ok=True, output=output)

    @classmethod
    def failure(cls, task_id: str, agent: str, error: str) -> "AgentResult":
        return cls(task_id=task_id, agent=agent, ok=False, error=error)


@dataclass
class AgentMessage:
    id: str
    topic: str
    sender: str
    payload: dict[str, Any] = field(default_factory=dict)
    ts: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def create(cls, topic: str, sender: str, payload: dict | None = None) -> "AgentMessage":
        return cls(id=new_id("msg"), topic=topic, sender=sender, payload=payload or {})
