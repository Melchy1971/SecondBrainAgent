"""Approval-gated writer base for all mutating connector actions."""

from __future__ import annotations

from typing import Any, Callable

from secondbrain.connectors.scaffold.approval import ApprovalGate


class ApprovalGatedWriter:
    resource = "generic"

    def __init__(self, client, gate: ApprovalGate) -> None:
        self.client = client
        self.gate = gate

    def _guarded(self, action: str, method: str, target: str, payload: Any, call: Callable[[], Any]) -> Any:
        return self.gate.guard(action=action, resource=self.resource, method=method,
                               target=target, payload=payload, execute=call)
