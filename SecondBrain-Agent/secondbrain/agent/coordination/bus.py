"""v30.69 Multi-Agent Coordination - CommunicationBus.

Synchronous in-process pub/sub with a message log. Agents subscribe to topics;
the coordinator publishes tasks and messages. Deterministic and auditable: every
message is appended to the log (and optionally persisted).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from .models import AgentMessage


class CommunicationBus:
    def __init__(self, project_root: str | Path | None = None):
        self.project_root = Path(project_root).resolve() if project_root else None
        self._subscribers: dict[str, list[Callable[[AgentMessage], Any]]] = {}
        self.log: list[AgentMessage] = []

    @property
    def _log_path(self) -> Path | None:
        if self.project_root is None:
            return None
        return self.project_root / "runtime" / "agent" / "coordination" / "bus.jsonl"

    def subscribe(self, topic: str, handler: Callable[[AgentMessage], Any]) -> None:
        self._subscribers.setdefault(topic, []).append(handler)

    def publish(self, topic: str, sender: str, payload: dict | None = None) -> list[Any]:
        message = AgentMessage.create(topic, sender, payload)
        self.log.append(message)
        self._persist(message)
        results = []
        for handler in self._subscribers.get(topic, []):
            results.append(handler(message))
        return results

    def messages(self, topic: str | None = None) -> list[AgentMessage]:
        if topic is None:
            return list(self.log)
        return [m for m in self.log if m.topic == topic]

    def _persist(self, message: AgentMessage) -> None:
        path = self._log_path
        if path is None:
            return
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(message.to_dict(), ensure_ascii=False) + "\n")
        except Exception:
            pass
