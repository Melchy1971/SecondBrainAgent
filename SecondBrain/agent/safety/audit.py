"""v30.61 Agent Safety Layer - ApprovalAudit.

Thin wrapper over the canonical :class:`NativeActionAuditLog`. The safety layer
never opens its own audit file; it writes into ``runtime/native/action_audit.jsonl``
so approvals and executed actions share one immutable trail.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from secondbrain.native.approval import NativeActionAuditLog

# Prefix that tags every safety-layer audit event in the shared trail.
SAFETY_INTENT_PREFIX = "safety."


class ApprovalAudit:
    def __init__(self, project_root: str | Path, log: NativeActionAuditLog | None = None):
        self.project_root = Path(project_root).resolve()
        self.log = log or NativeActionAuditLog(self.project_root)

    @property
    def path(self) -> Path:
        return self.log.path

    def write(
        self,
        *,
        actor: str,
        action: str,
        event: str,
        outcome: str,
        reason: str = "",
        approval_id: str = "",
        risk_level: str = "",
        ok: bool = True,
        requires_approval: bool = False,
        executed: bool = False,
    ) -> dict[str, Any]:
        """Append one safety event to the shared native audit trail."""

        note = f"by {actor}"
        if risk_level:
            note += f" | risk={risk_level}"
        if reason:
            note += f" | {reason}"
        payload = {
            "command": action,
            "intent": f"{SAFETY_INTENT_PREFIX}{event}",
            "text": note,
            "status": outcome,
            "ok": ok,
            "requires_confirmation": requires_approval,
            "executed": executed,
            "target": approval_id,
        }
        return self.log.append(payload, confirmed=ok and not requires_approval)

    def events(self, limit: int = 50, *, safety_only: bool = True) -> list[dict[str, Any]]:
        rows = self.log.latest(limit=max(1, int(limit)) if not safety_only else 500)
        if safety_only:
            rows = [r for r in rows if str(r.get("intent", "")).startswith(SAFETY_INTENT_PREFIX)]
            rows = rows[: max(1, int(limit))]
        return rows
