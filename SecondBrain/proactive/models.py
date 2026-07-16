"""Data model for proactive, evidence-based suggestions.

A suggestion is a proposal, never an action. It carries the evidence and
confidence that justify it, a proposed_action describing what *could* be done
(create a task or plan - executed only after the user accepts), an expiry, and
a status through its lifecycle. Nothing here performs an external action.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

__all__ = ["SuggestionCategory", "SuggestionStatus", "Priority", "SuggestionRule", "Suggestion", "FeedbackRecord"]


class SuggestionCategory(StrEnum):
    DEADLINE_RISK = "deadline_risk"
    OVERDUE_TASK = "overdue_task"
    MISSING_PREPARATION = "missing_preparation"
    BLOCKED_PROJECT = "blocked_project"
    UNANSWERED_MESSAGE = "unanswered_message"
    CALENDAR_CONFLICT = "calendar_conflict"
    CONTRACT_EXPIRY = "contract_expiry"
    CONNECTOR_PROBLEM = "connector_problem"
    KNOWLEDGE_CONFLICT = "knowledge_conflict"
    OVERDUE_APPROVAL = "overdue_approval"
    MISSING_BACKUP = "missing_backup"
    RECURRING_PATTERN = "recurring_pattern"
    STALE_MEMORY = "stale_memory"
    FAILED_JOB = "failed_job"
    CAPACITY_RISK = "capacity_risk"


class SuggestionStatus(StrEnum):
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    ACCEPTED = "accepted"
    DISMISSED = "dismissed"
    SNOOZED = "snoozed"
    EXPIRED = "expired"


class Priority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Suggestion:
    suggestion_id: str
    workspace_id: str
    category: str
    title: str
    description: str = ""
    evidence: list[dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.5
    priority: str = Priority.MEDIUM.value
    proposed_action: dict[str, Any] = field(default_factory=dict)
    expires_at: str = ""
    status: str = SuggestionStatus.NEW.value
    created_at: str = ""
    dedup_key: str = ""
    source_references: list[str] = field(default_factory=list)
    snoozed_until: str = ""
    rule_id: str = ""
    version: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "suggestion_id": self.suggestion_id, "workspace_id": self.workspace_id,
            "category": self.category, "title": self.title, "description": self.description,
            "evidence": [dict(e) for e in self.evidence], "confidence": round(float(self.confidence), 3),
            "priority": self.priority, "proposed_action": dict(self.proposed_action),
            "expires_at": self.expires_at, "status": self.status, "created_at": self.created_at,
            "dedup_key": self.dedup_key,
            "source_references": list(self.source_references), "snoozed_until": self.snoozed_until,
            "rule_id": self.rule_id, "version": self.version,
        }


@dataclass
class SuggestionRule:
    rule_id: str
    category: str
    conditions: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    confidence_threshold: float = 0.5
    cooldown_minutes: int = 7 * 24 * 60
    priority: str = Priority.MEDIUM.value
    maximum_open_items: int = 3
    workspace_scope: str = "*"
    created_at: str = ""
    updated_at: str = ""

    @property
    def cooldown_days(self) -> float:
        return self.cooldown_minutes / (24 * 60)

    @property
    def max_open_suggestions(self) -> int:
        return self.maximum_open_items


@dataclass
class FeedbackRecord:
    at: str
    suggestion_id: str
    dedup_key: str
    category: str
    action: str              # accepted | dismissed | snoozed | acknowledged
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"at": self.at, "suggestion_id": self.suggestion_id, "dedup_key": self.dedup_key,
                "category": self.category, "action": self.action, "detail": self.detail}
