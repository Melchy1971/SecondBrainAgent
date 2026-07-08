"""v30.61 Agent Safety Layer - ActionGuard and SafetyService.

``SafetyService`` is the façade that wires the classifier, policy, the canonical
:class:`NativeApprovalQueue` and the shared audit trail together. ``ActionGuard``
is the single entry point an agent calls *before* performing a risky action.

Design contract (v30.61 brief):
* No second approval queue - all approvals live in the existing
  ``runtime/native/approval_queue.jsonl`` written by ``NativeApprovalQueue``.
* Every guarded action, allowed or not, produces one audit event.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from secondbrain.native.approval import NativeApprovalQueue

from .audit import ApprovalAudit
from .models import APPROVED, EXPIRED, PENDING, REJECTED, ApprovalDecision, GuardDecision
from .policy import ALLOW, BLOCK, REQUIRE_APPROVAL, SafetyPolicy
from .risk import RiskClassifier

# Approvals left pending longer than this default are eligible to expire.
DEFAULT_TTL_SECONDS = 24 * 60 * 60


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_ts(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


class SafetyService:
    """Approval lifecycle on top of the canonical native queue."""

    def __init__(
        self,
        project_root: str | Path,
        *,
        policy: SafetyPolicy | None = None,
        classifier: RiskClassifier | None = None,
        queue: NativeApprovalQueue | None = None,
        audit: ApprovalAudit | None = None,
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
    ):
        self.project_root = Path(project_root).resolve()
        self.policy = policy or SafetyPolicy()
        self.classifier = classifier or RiskClassifier()
        self.queue = queue or NativeApprovalQueue(self.project_root)
        self.audit = audit or ApprovalAudit(self.project_root)
        self.ttl_seconds = int(ttl_seconds)

    # -- introspection -----------------------------------------------------
    def policy_check(self, action: str, *, risk_hint: str | None = None):
        risk_level = self.classifier.classify(action, hint=risk_hint)
        return risk_level, self.policy.evaluate(action, risk_level)

    def list(self, *, status: str | None = None) -> list[dict[str, Any]]:
        return self.queue.list(status=status)

    def get(self, approval_id: str) -> dict[str, Any] | None:
        return self.queue.get(approval_id)

    def audit_events(self, limit: int = 50, *, safety_only: bool = True) -> list[dict[str, Any]]:
        return self.audit.events(limit=limit, safety_only=safety_only)

    # -- lifecycle ---------------------------------------------------------
    def request(
        self,
        *,
        actor: str,
        action: str,
        intent: str = "",
        text: str = "",
        target: str = "",
        risk_hint: str | None = None,
    ) -> dict[str, Any]:
        """Create a pending approval in the existing queue and audit it."""

        risk_level, verdict = self.policy_check(action, risk_hint=risk_hint)
        reason = verdict.reason
        record = self.queue.create(
            command=action,
            intent=intent or action,
            text=text or action,
            target=target,
            risk_level=risk_level,
            reason=reason,
        )
        self.audit.write(
            actor=actor,
            action=action,
            event="request",
            outcome=PENDING,
            reason=reason,
            approval_id=record["approval_id"],
            risk_level=risk_level,
            ok=True,
            requires_approval=True,
        )
        return record

    def _decide(self, approval_id: str, status: str, decided_by: str, event: str) -> ApprovalDecision:
        decided_at = _utc_now().isoformat(timespec="seconds")
        record = self.queue.mark(approval_id, status)
        if record is None:
            self.audit.write(
                actor=decided_by,
                action="approval",
                event=event,
                outcome="not_found",
                approval_id=approval_id,
                ok=False,
            )
            return ApprovalDecision.not_found(approval_id, decided_by, decided_at)
        self.audit.write(
            actor=decided_by,
            action=str(record.get("command", "approval")),
            event=event,
            outcome=status,
            reason=str(record.get("reason", "")),
            approval_id=approval_id,
            risk_level=str(record.get("risk_level", "")),
            ok=True,
        )
        return ApprovalDecision(
            approval_id=approval_id,
            status=status,
            decided_by=decided_by,
            decided_at=decided_at,
            ok=True,
            record=record,
        )

    def approve(self, approval_id: str, *, decided_by: str = "user") -> ApprovalDecision:
        return self._decide(approval_id, APPROVED, decided_by, "approve")

    def reject(self, approval_id: str, *, decided_by: str = "user") -> ApprovalDecision:
        return self._decide(approval_id, REJECTED, decided_by, "reject")

    def expire(
        self,
        *,
        ttl_seconds: int | None = None,
        now: datetime | None = None,
        decided_by: str = "system",
    ) -> list[ApprovalDecision]:
        """Mark every pending approval older than the TTL as expired."""

        ttl = self.ttl_seconds if ttl_seconds is None else int(ttl_seconds)
        current = now or _utc_now()
        decisions: list[ApprovalDecision] = []
        for row in self.queue.list(status=PENDING):
            created = _parse_ts(str(row.get("created_at", "")))
            if created is None:
                continue
            if (current - created).total_seconds() >= ttl:
                decisions.append(
                    self._decide(row["approval_id"], EXPIRED, decided_by, "expire")
                )
        return decisions


class ActionGuard:
    """Gate an action through classification, policy and (if needed) approval."""

    def __init__(self, project_root: str | Path, *, service: SafetyService | None = None, **kwargs: Any):
        self.project_root = Path(project_root).resolve()
        self.service = service or SafetyService(self.project_root, **kwargs)

    @property
    def policy(self) -> SafetyPolicy:
        return self.service.policy

    @property
    def classifier(self) -> RiskClassifier:
        return self.service.classifier

    def guard(
        self,
        *,
        actor: str,
        action: str,
        intent: str = "",
        text: str = "",
        target: str = "",
        risk_hint: str | None = None,
    ) -> GuardDecision:
        risk_level = self.classifier.classify(action, hint=risk_hint)
        verdict = self.policy.evaluate(action, risk_level)

        if verdict.outcome == BLOCK:
            self.service.audit.write(
                actor=actor,
                action=action,
                event="block",
                outcome=BLOCK,
                reason=verdict.reason,
                risk_level=risk_level,
                ok=False,
            )
            return GuardDecision(
                actor=actor,
                action=action,
                risk_level=risk_level,
                outcome=BLOCK,
                reason=verdict.reason,
                allowed=False,
            )

        if verdict.outcome == ALLOW:
            self.service.audit.write(
                actor=actor,
                action=action,
                event="allow",
                outcome=ALLOW,
                reason=verdict.reason,
                risk_level=risk_level,
                ok=True,
                executed=True,
            )
            return GuardDecision(
                actor=actor,
                action=action,
                risk_level=risk_level,
                outcome=ALLOW,
                reason=verdict.reason,
                allowed=True,
            )

        # REQUIRE_APPROVAL: reuse an open pending approval for the same target
        # if one exists, otherwise create one in the existing queue.
        record = self._find_open(action, target)
        if record is None:
            record = self.service.request(
                actor=actor,
                action=action,
                intent=intent,
                text=text,
                target=target,
                risk_hint=risk_hint,
            )
        return GuardDecision(
            actor=actor,
            action=action,
            risk_level=risk_level,
            outcome=REQUIRE_APPROVAL,
            reason=verdict.reason,
            allowed=False,
            approval_id=record["approval_id"],
            approval=record,
        )

    def _find_open(self, action: str, target: str) -> dict[str, Any] | None:
        if not target:
            return None
        for row in self.service.queue.list(status=PENDING):
            if row.get("command") == action and row.get("target") == target:
                return row
        return None
