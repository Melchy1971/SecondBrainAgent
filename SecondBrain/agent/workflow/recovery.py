"""v30.62 Agent Workflow Engine - WorkflowRecovery.

Decides what to do when a step raises. Reuses the classification logic of the
existing ``secondbrain.agent.workflow_recovery.WorkflowRecovery`` (timeout ->
retry, approval -> wait) and extends it with an attempt-aware verdict so the
executor knows whether to retry, escalate to approval, prepare a rollback or
fail fast.
"""

from __future__ import annotations

from dataclasses import dataclass

from secondbrain.agent.workflow_recovery import WorkflowRecovery as _BaseRecovery

# Recovery strategies.
RETRY = "RETRY"
WAIT_FOR_APPROVAL = "WAIT_FOR_APPROVAL"
ROLLBACK = "ROLLBACK"
FAIL_FAST = "FAIL_FAST"


@dataclass(frozen=True)
class RecoveryVerdict:
    strategy: str
    reason: str
    attempt: int
    max_retries: int

    @property
    def should_retry(self) -> bool:
        return self.strategy == RETRY

    def to_dict(self) -> dict:
        return {
            "strategy": self.strategy,
            "reason": self.reason,
            "attempt": self.attempt,
            "max_retries": self.max_retries,
        }


class WorkflowRecovery:
    def __init__(self) -> None:
        self._base = _BaseRecovery()

    def classify(self, error: Exception) -> dict:
        # Preserve the base contract for callers/tests that expect the raw dict.
        return self._base.classify(error)

    def decide(self, error: Exception, *, attempt: int, max_retries: int) -> RecoveryVerdict:
        base = self._base.classify(error)
        strategy = base["strategy"]
        reason = base["reason"]

        # Type-based safety net: a real TimeoutError is retryable even if its
        # message does not contain the word "timeout".
        if isinstance(error, TimeoutError) and strategy != WAIT_FOR_APPROVAL:
            strategy = RETRY
            if base["strategy"] != RETRY:
                reason = "timeout_type"

        if strategy == WAIT_FOR_APPROVAL:
            return RecoveryVerdict(WAIT_FOR_APPROVAL, reason, attempt, max_retries)

        # Retryable errors retry until the budget is exhausted, then roll back.
        if strategy == RETRY:
            if attempt < max_retries:
                return RecoveryVerdict(RETRY, reason, attempt, max_retries)
            return RecoveryVerdict(ROLLBACK, "retry_budget_exhausted", attempt, max_retries)

        # Unknown / fail-fast: still honour a remaining retry budget once, then
        # prepare rollback rather than leaving the workflow half-applied.
        if attempt < max_retries:
            return RecoveryVerdict(RETRY, reason, attempt, max_retries)
        return RecoveryVerdict(ROLLBACK, reason, attempt, max_retries)
