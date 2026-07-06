"""v30.61 Agent Safety Layer - value objects.

``ApprovalRequest`` is intentionally re-exported from the canonical native queue
module rather than redefined here: the safety layer never owns a second request
schema. ``ApprovalDecision`` and ``GuardDecision`` are new, and describe the
outcome of a decision and of an ActionGuard evaluation respectively.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Re-export the ONE canonical approval record type. Any code importing
# ApprovalRequest from the safety package gets the exact same class the native
# queue writes, guaranteeing there is no divergent second definition.
from secondbrain.native.approval import ApprovalRequest  # noqa: F401

# Terminal decision states an approval can reach.
APPROVED = "approved"
REJECTED = "rejected"
EXPIRED = "expired"
PENDING = "pending"


@dataclass(frozen=True)
class ApprovalDecision:
    """Result of approving, rejecting or expiring a queued approval."""

    approval_id: str
    status: str
    decided_by: str
    decided_at: str
    ok: bool = True
    error: str = ""
    record: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "approval_id": self.approval_id,
            "status": self.status,
            "decided_by": self.decided_by,
            "decided_at": self.decided_at,
            "ok": self.ok,
            "error": self.error,
            "record": self.record,
        }

    @classmethod
    def not_found(cls, approval_id: str, decided_by: str, decided_at: str) -> "ApprovalDecision":
        return cls(
            approval_id=approval_id,
            status="not_found",
            decided_by=decided_by,
            decided_at=decided_at,
            ok=False,
            error="approval_not_found",
            record=None,
        )


@dataclass(frozen=True)
class GuardDecision:
    """Outcome of ActionGuard.guard for a single requested action."""

    actor: str
    action: str
    risk_level: str
    outcome: str  # allow / require_approval / block
    reason: str
    allowed: bool
    approval_id: str | None = None
    approval: dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "actor": self.actor,
            "action": self.action,
            "risk_level": self.risk_level,
            "outcome": self.outcome,
            "reason": self.reason,
            "allowed": self.allowed,
            "approval_id": self.approval_id,
            "approval": self.approval,
            "metadata": self.metadata,
        }
