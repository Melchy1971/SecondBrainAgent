"""v30.61 Agent Approval & Safety Layer.

Central, reusable guard rail for risky agent actions. Everything routes through
the existing native approval queue (``runtime/native/approval_queue.jsonl``) and
the shared native audit trail - there is no second queue.

Public surface:
    RiskClassifier   - action -> risk level (read/low/medium/high/destructive/external)
    SafetyPolicy     - risk level -> allow / require_approval / block
    ActionGuard      - gate one action end to end
    SafetyService    - approval lifecycle (request/approve/reject/expire/audit)
    ApprovalAudit    - safety events on the shared audit trail
    ApprovalRequest  - canonical queue record (re-exported, not redefined)
    ApprovalDecision / GuardDecision / PolicyVerdict - value objects
"""

from __future__ import annotations

from .audit import ApprovalAudit
from .guard import DEFAULT_TTL_SECONDS, ActionGuard, SafetyService
from .models import (
    APPROVED,
    DEFERRED,
    EXPIRED,
    PENDING,
    REJECTED,
    ApprovalDecision,
    ApprovalItem,
    ApprovalRequest,
    GuardDecision,
    ReviewItem,
)
from .policy import ALLOW, BLOCK, REQUIRE_APPROVAL, PolicyVerdict, SafetyPolicy
from .risk import RISK_LEVELS, RiskClassifier

__all__ = [
    "RiskClassifier",
    "RISK_LEVELS",
    "SafetyPolicy",
    "PolicyVerdict",
    "ALLOW",
    "REQUIRE_APPROVAL",
    "BLOCK",
    "ActionGuard",
    "SafetyService",
    "DEFAULT_TTL_SECONDS",
    "ApprovalAudit",
    "ApprovalRequest",
    "ApprovalItem",
    "ReviewItem",
    "ApprovalDecision",
    "GuardDecision",
    "APPROVED",
    "DEFERRED",
    "REJECTED",
    "EXPIRED",
    "PENDING",
]
