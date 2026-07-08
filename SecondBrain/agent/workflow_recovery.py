"""v30.3 - workflow recovery strategy."""

from __future__ import annotations


class WorkflowRecovery:
    def classify(self, error: Exception) -> dict:
        text = str(error).lower()
        if "timeout" in text:
            return {"strategy": "RETRY", "reason": "timeout"}
        if "approval" in text:
            return {"strategy": "WAIT_FOR_APPROVAL", "reason": "approval_required"}
        return {"strategy": "FAIL_FAST", "reason": "unknown"}
