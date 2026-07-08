"""P2 v21.2 - Tool Invocation Audit."""

from time import time


class ToolInvocationAudit:
    def __init__(self):
        self._events = []

    def record(self, tool_name: str, status: str):
        self._events.append({
            "tool": tool_name,
            "status": status,
            "timestamp": time(),
        })

    def list(self):
        return list(self._events)
