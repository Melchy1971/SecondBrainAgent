"""Mail assistant data model."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any

__all__ = ["Category", "MailMessage", "MailThread", "PriorityScore"]


class Category(StrEnum):
    ACTION_REQUIRED = "action_required"
    WAITING_FOR_REPLY = "waiting_for_reply"
    INFORMATION = "information"
    MEETING = "meeting"
    INVOICE = "invoice"
    CONTRACT = "contract"
    PROJECT = "project"
    PERSONAL = "personal"
    LOW_PRIORITY = "low_priority"
    SPAM_CANDIDATE = "spam_candidate"


@dataclass
class MailMessage:
    message_id: str
    thread_id: str
    mailbox_id: str
    workspace_id: str
    sender: str
    recipients: list[str]
    subject: str
    body: str = ""
    received_at: str = ""
    unread: bool = True
    has_attachments: bool = False
    attachments: list[str] = field(default_factory=list)  # file names only, never content
    external_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MailMessage":
        return cls(**{k: data.get(k) for k in cls.__dataclass_fields__ if k in data})


@dataclass
class MailThread:
    thread_id: str
    mailbox_id: str
    workspace_id: str
    subject: str
    participants: list[str] = field(default_factory=list)
    latest_message_at: str = ""
    unread_count: int = 0
    importance_score: float = 0.0
    action_required: bool = False
    due_date: str | None = None
    category: str = Category.INFORMATION.value
    summary: str = ""
    source: str = "connector"
    external_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MailThread":
        return cls(**{k: data.get(k) for k in cls.__dataclass_fields__ if k in data})


@dataclass
class PriorityScore:
    score: float
    factors: dict[str, float]

    def to_dict(self) -> dict[str, Any]:
        return {"score": round(self.score, 3), "factors": {k: round(v, 3) for k, v in self.factors.items()}}
