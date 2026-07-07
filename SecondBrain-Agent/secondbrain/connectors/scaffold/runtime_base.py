"""Base runtime facade for connector providers (login/sync/status/disconnect)."""

from __future__ import annotations

import time
from typing import Any, Callable

from secondbrain.connectors.scaffold.sync import BackgroundSync


class ConnectorRuntime:
    def __init__(self, *, provider: str, resource_names, auth, client, cursor_store, gate, sink,
                 build_connectors: Callable, build_writers: Callable, cursor_prefix: str | None = None) -> None:
        self.provider = provider
        self.resource_names = tuple(resource_names)
        self.auth = auth
        self.client = client
        self.cursor_store = cursor_store
        self.gate = gate
        self.sink = sink
        self._build_connectors = build_connectors
        self._build_writers = build_writers
        self.cursor_prefix = cursor_prefix or provider

    def login(self, *, printer: Callable[[str], None] | None = None, wait: bool = True,
              sleeper: Callable[[float], None] = time.sleep) -> dict[str, Any]:
        start = self.auth.begin_device_login()
        message = start.message or f"Open {start.verification_uri} and enter code {start.user_code}"
        if printer:
            printer(message)
        if not wait:
            return {"status": "pending", "instructions": start.to_public_dict()}
        self.auth.complete_device_login(start, sleeper=sleeper)
        return {"status": "ok", **self.auth.status()}

    def sync(self, resources=None) -> dict[str, Any]:
        connectors = self._build_connectors(self.client, resources)
        bg = BackgroundSync(connectors, sink=self.sink, cursor_store=self.cursor_store)
        return {"status": "ok", "results": bg.run_once()}

    def status(self) -> dict[str, Any]:
        st = self.auth.status()
        st["resources"] = list(self.resource_names)
        st["pending_approvals"] = len(self.gate.pending())
        cursors = {}
        for name in self.resource_names:
            cur = self.cursor_store.get(f"{self.cursor_prefix}_{name}")
            cursors[name] = cur.value if cur else None
        st["cursors"] = cursors
        return st

    def disconnect(self, *, purge_cursors: bool = True) -> dict[str, Any]:
        was_auth = self.auth.forget()
        if purge_cursors:
            for name in self.resource_names:
                self.cursor_store.delete(f"{self.cursor_prefix}_{name}")
        return {"status": "ok", "was_authenticated": was_auth}

    def writers(self) -> dict[str, Any]:
        return self._build_writers(self.client, self.gate)

    def pending_approvals(self) -> list[dict]:
        return [r.to_dict() for r in self.gate.pending()]

    def approve(self, request_id: str) -> dict[str, Any]:
        r = self.gate.approve(request_id)
        return {"status": "ok" if r else "not_found", "request": r.to_dict() if r else None}
