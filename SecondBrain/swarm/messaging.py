
from __future__ import annotations
from pathlib import Path
from typing import Any
from .common import JsonStore, new_id, now_iso

class AgentMessageBus:
    def __init__(self, runtime_dir: str | Path, event_bus: Any | None = None):
        self.store = JsonStore(Path(runtime_dir) / "swarm_v124" / "messages.json", [])
        self.event_bus = event_bus

    def send(self, task_id: str, sender: str, recipient: str, message_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        row = {"id": new_id("msg"), "task_id": task_id, "sender": sender, "recipient": recipient, "type": message_type, "payload": payload, "created_at": now_iso()}
        self.store.append(row)
        if self.event_bus:
            self.event_bus.publish("swarm.message.created", "swarm_v124", row, risk_level=1, correlation_id=task_id)
        return row

    def list(self, task_id: str | None = None) -> list[dict[str, Any]]:
        rows = self.store.read()
        return [r for r in rows if r.get("task_id") == task_id] if task_id else rows

    def status(self) -> dict[str, Any]:
        return {"component": "agent_message_bus_v124", "messages": len(self.store.read()), "healthy": True}
