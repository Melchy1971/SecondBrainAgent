from __future__ import annotations
from dataclasses import dataclass
from .state_models import UiState

@dataclass(frozen=True)
class AuditIssue:
    code: str
    message: str
    severity: str = "warning"

class AccessibilityAudit:
    def audit_state(self, state: UiState) -> list[AuditIssue]:
        issues: list[AuditIssue] = []
        if not state.title.strip():
            issues.append(AuditIssue("missing_title", "UI state has no title", "error"))
        if not state.message.strip():
            issues.append(AuditIssue("missing_message", "UI state has no message", "error"))
        if state.is_blocking() and not state.recovery_action:
            issues.append(AuditIssue("missing_recovery", "Blocking state has no recovery action", "error"))
        if state.hint is None:
            issues.append(AuditIssue("missing_a11y_hint", "UI state has no accessibility hint"))
        elif not state.hint.label.strip():
            issues.append(AuditIssue("missing_a11y_label", "Accessibility hint has no label", "error"))
        return issues

    def passes(self, state: UiState) -> bool:
        return not any(issue.severity == "error" for issue in self.audit_state(state))
