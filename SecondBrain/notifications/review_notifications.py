"""Notifications and escalation for pending review/approval items.

This module turns the *state* of the unified review inbox into actionable
notifications and escalates the ones that sit too long or carry high risk.

Two entry points:

* :meth:`ReviewNotificationService.evaluate` - a pull/polling pass over the
  current inbox items. It is idempotent within a cooldown window
  (``escalation_interval``) so repeated snapshots do not spam duplicates, and it
  respects acknowledgement and snooze state.
* :meth:`ReviewNotificationService.record_decision` - an event hook fired when a
  decision is taken, producing a ``decision_recorded`` notification.

No notification ever contains raw secrets: every title/message passes through
:class:`~secondbrain.agent.privacy.PrivacyGuard` redaction.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import StrEnum
from hashlib import sha256
from pathlib import Path
from typing import Any, Iterable, Mapping

from secondbrain.agent.privacy import PrivacyDecision, PrivacyGuard, PrivacyMode

__all__ = [
    "NotificationType",
    "NotificationPriority",
    "TimeRules",
    "ReviewNotification",
    "ReviewNotificationService",
    "ESCALATION_RULES",
    "priority_for",
]


class NotificationType(StrEnum):
    APPROVAL_REQUESTED = "approval_requested"
    CRITICAL_APPROVAL_REQUESTED = "critical_approval_requested"
    REVIEW_REQUIRED = "review_required"
    REVIEW_OVERDUE = "review_overdue"
    DEFERRED_ITEM_DUE = "deferred_item_due"
    APPROVAL_EXPIRING = "approval_expiring"
    APPROVAL_EXPIRED = "approval_expired"
    DECISION_RECORDED = "decision_recorded"


class NotificationPriority(StrEnum):
    INFO = "info"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


_PRIORITY_RANK = {
    NotificationPriority.INFO: 0,
    NotificationPriority.NORMAL: 1,
    NotificationPriority.HIGH: 2,
    NotificationPriority.CRITICAL: 3,
}

# Escalation by category / change type. Keys are matched case-insensitively.
ESCALATION_RULES: dict[str, NotificationPriority] = {
    "delete_request": NotificationPriority.HIGH,
    "connector_permission_change": NotificationPriority.HIGH,
    "credential_change": NotificationPriority.CRITICAL,
    "external_send": NotificationPriority.HIGH,
    "sensitive_document": NotificationPriority.HIGH,
    "failed_import": NotificationPriority.NORMAL,
    "low_confidence_classification": NotificationPriority.NORMAL,
}

_RISK_PRIORITY: dict[str, NotificationPriority] = {
    "critical": NotificationPriority.CRITICAL,
    "destructive": NotificationPriority.HIGH,
    "high": NotificationPriority.HIGH,
    "write": NotificationPriority.NORMAL,
    "read": NotificationPriority.INFO,
    "low": NotificationPriority.INFO,
}

_SECRET_GUARD = PrivacyGuard(PrivacyMode.OFF)


def priority_for(
    *,
    category: str = "",
    risk_level: str = "",
    change_type: str = "",
) -> NotificationPriority:
    """Resolve the escalation priority from the strongest available signal."""

    for key in (change_type, category):
        rule = ESCALATION_RULES.get(str(key).strip().lower())
        if rule is not None:
            return rule
    return _RISK_PRIORITY.get(str(risk_level).strip().lower(), NotificationPriority.NORMAL)


def _max_priority(a: NotificationPriority, b: NotificationPriority) -> NotificationPriority:
    return a if _PRIORITY_RANK[a] >= _PRIORITY_RANK[b] else b


@dataclass(frozen=True)
class TimeRules:
    """All durations configurable; defaults chosen for a working day."""

    warning_after: timedelta = timedelta(hours=1)
    overdue_after: timedelta = timedelta(hours=4)
    approval_expiration: timedelta = timedelta(hours=24)
    deferred_reminder: timedelta = timedelta(hours=1)
    escalation_interval: timedelta = timedelta(hours=1)
    expiring_window: timedelta = timedelta(hours=2)


@dataclass(frozen=True)
class ReviewNotification:
    id: str
    type: NotificationType
    priority: NotificationPriority
    item_id: str
    item_type: str
    category: str
    title: str
    message: str
    deep_link: str
    created_at: str
    dedup_key: str
    system_critical: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "priority": self.priority.value,
            "item_id": self.item_id,
            "item_type": self.item_type,
            "category": self.category,
            "title": self.title,
            "message": self.message,
            "deep_link": self.deep_link,
            "created_at": self.created_at,
            "dedup_key": self.dedup_key,
            "system_critical": self.system_critical,
            "metadata": dict(self.metadata),
        }


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_ts(value: str) -> datetime | None:
    text = (value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _redact(text: str) -> str:
    result = _SECRET_GUARD.inspect_memory_write(text or "")
    if result.reason == "secret_redacted" and result.decision != PrivacyDecision.ALLOW:
        return result.redacted_text or "[REDACTED_SECRET]"
    return text or ""


class ReviewNotificationService:
    def __init__(
        self,
        *,
        time_rules: TimeRules | None = None,
        state_path: str | Path | None = None,
        deep_link_base: str = "secondbrain://inbox",
    ) -> None:
        self.time_rules = time_rules or TimeRules()
        self.deep_link_base = deep_link_base.rstrip("/")
        self._state_path = Path(state_path).resolve() if state_path is not None else None
        # dedup_key -> {"acknowledged": bool, "snoozed_until": iso, "last_emitted": iso}
        self._state: dict[str, dict[str, Any]] = {}
        self._load_state()

    # -- public API -------------------------------------------------------

    def evaluate(
        self,
        items: Iterable[Mapping[str, Any]],
        *,
        now: datetime | None = None,
    ) -> list[ReviewNotification]:
        moment = now or _utc_now()
        emitted: list[ReviewNotification] = []
        for item in items:
            notification = self._notification_for(item, moment)
            if notification is None:
                continue
            if self._suppressed(notification.dedup_key, moment):
                continue
            self._mark_emitted(notification.dedup_key, moment)
            emitted.append(notification)
        self._save_state()
        return emitted

    def record_decision(
        self,
        item: Mapping[str, Any],
        status: str,
        *,
        now: datetime | None = None,
    ) -> ReviewNotification:
        moment = now or _utc_now()
        item_id = str(item.get("item_id") or item.get("review_id") or item.get("approval_id") or "")
        category = str(item.get("category") or "")
        title = _redact(str(item.get("title") or ""))
        dedup = _dedup_key(NotificationType.DECISION_RECORDED, item_id, status)
        notification = ReviewNotification(
            id=dedup,
            type=NotificationType.DECISION_RECORDED,
            priority=NotificationPriority.INFO,
            item_id=item_id,
            item_type=str(item.get("item_type") or ""),
            category=category,
            title=title,
            message=_redact(f"Entscheidung '{status}' erfasst"),
            deep_link=self._deep_link(item_id),
            created_at=moment.isoformat(timespec="seconds"),
            dedup_key=dedup,
            metadata={"status": status},
        )
        return notification

    def acknowledge(self, dedup_key: str) -> None:
        entry = self._state.setdefault(dedup_key, {})
        entry["acknowledged"] = True
        self._save_state()

    def snooze(self, dedup_key: str, until: datetime | str) -> None:
        iso = until.isoformat(timespec="seconds") if isinstance(until, datetime) else str(until)
        entry = self._state.setdefault(dedup_key, {})
        entry["snoozed_until"] = iso
        self._save_state()

    def is_acknowledged(self, dedup_key: str) -> bool:
        return bool(self._state.get(dedup_key, {}).get("acknowledged"))

    def badge_count(self, items: Iterable[Mapping[str, Any]], *, now: datetime | None = None) -> int:
        moment = now or _utc_now()
        count = 0
        for item in items:
            notification = self._notification_for(item, moment)
            if notification is None:
                continue
            if self.is_acknowledged(notification.dedup_key):
                continue
            if self._snoozed(notification.dedup_key, moment):
                continue
            if _PRIORITY_RANK[notification.priority] >= _PRIORITY_RANK[NotificationPriority.HIGH]:
                count += 1
        return count

    # -- notification derivation -----------------------------------------

    def _notification_for(
        self,
        item: Mapping[str, Any],
        now: datetime,
    ) -> ReviewNotification | None:
        status = str(item.get("status") or "").strip().lower()
        item_id = str(item.get("item_id") or "")
        item_type = str(item.get("item_type") or "")
        category = str(item.get("category") or "")
        change_type = str(item.get("change_type") or "")
        risk_level = str(item.get("risk_level") or "")
        title = _redact(str(item.get("title") or ""))
        created = _parse_ts(str(item.get("created_at") or ""))
        base_priority = priority_for(category=category, risk_level=risk_level, change_type=change_type)

        if status == "deferred":
            due = _parse_ts(str(item.get("deferred_until") or ""))
            if due is not None and now >= due:
                return self._build(NotificationType.DEFERRED_ITEM_DUE, base_priority, item, title, now)
            return None

        if status != "pending":
            return None

        age = (now - created) if created is not None else timedelta(0)

        # Expiry takes precedence over routine reminders for approvals.
        if item_type == "approval":
            if age >= self.time_rules.approval_expiration:
                return self._build(
                    NotificationType.APPROVAL_EXPIRED,
                    _max_priority(base_priority, NotificationPriority.HIGH),
                    item,
                    title,
                    now,
                )
            if age >= (self.time_rules.approval_expiration - self.time_rules.expiring_window):
                return self._build(
                    NotificationType.APPROVAL_EXPIRING,
                    _max_priority(base_priority, NotificationPriority.HIGH),
                    item,
                    title,
                    now,
                )

        if age >= self.time_rules.overdue_after:
            return self._build(
                NotificationType.REVIEW_OVERDUE,
                _max_priority(base_priority, NotificationPriority.HIGH),
                item,
                title,
                now,
            )

        if item_type == "approval":
            ntype = (
                NotificationType.CRITICAL_APPROVAL_REQUESTED
                if base_priority == NotificationPriority.CRITICAL
                else NotificationType.APPROVAL_REQUESTED
            )
            return self._build(ntype, base_priority, item, title, now)

        return self._build(NotificationType.REVIEW_REQUIRED, base_priority, item, title, now)

    def _build(
        self,
        ntype: NotificationType,
        priority: NotificationPriority,
        item: Mapping[str, Any],
        title: str,
        now: datetime,
    ) -> ReviewNotification:
        item_id = str(item.get("item_id") or "")
        dedup = _dedup_key(ntype, item_id, priority.value)
        system_critical = priority == NotificationPriority.CRITICAL
        return ReviewNotification(
            id=dedup,
            type=ntype,
            priority=priority,
            item_id=item_id,
            item_type=str(item.get("item_type") or ""),
            category=str(item.get("category") or ""),
            title=title,
            message=_redact(_message_for(ntype, title)),
            deep_link=self._deep_link(item_id),
            created_at=now.isoformat(timespec="seconds"),
            dedup_key=dedup,
            system_critical=system_critical,
        )

    def _deep_link(self, item_id: str) -> str:
        return f"{self.deep_link_base}/{item_id}" if item_id else self.deep_link_base

    # -- state ------------------------------------------------------------

    def _suppressed(self, dedup_key: str, now: datetime) -> bool:
        if self.is_acknowledged(dedup_key):
            return True
        if self._snoozed(dedup_key, now):
            return True
        return self._in_cooldown(dedup_key, now)

    def _snoozed(self, dedup_key: str, now: datetime) -> bool:
        until = _parse_ts(str(self._state.get(dedup_key, {}).get("snoozed_until") or ""))
        return until is not None and now < until

    def _in_cooldown(self, dedup_key: str, now: datetime) -> bool:
        last = _parse_ts(str(self._state.get(dedup_key, {}).get("last_emitted") or ""))
        if last is None:
            return False
        return (now - last) < self.time_rules.escalation_interval

    def _mark_emitted(self, dedup_key: str, now: datetime) -> None:
        entry = self._state.setdefault(dedup_key, {})
        entry["last_emitted"] = now.isoformat(timespec="seconds")

    def _load_state(self) -> None:
        if self._state_path is None or not self._state_path.exists():
            return
        try:
            data = json.loads(self._state_path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                self._state = {str(k): dict(v) for k, v in data.items() if isinstance(v, dict)}
        except (json.JSONDecodeError, OSError):
            self._state = {}

    def _save_state(self) -> None:
        if self._state_path is None:
            return
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        self._state_path.write_text(json.dumps(self._state, ensure_ascii=False, indent=2), encoding="utf-8")


def _dedup_key(ntype: NotificationType, item_id: str, discriminator: str) -> str:
    raw = "|".join([ntype.value, item_id, discriminator])
    return sha256(raw.encode("utf-8")).hexdigest()[:24]


_MESSAGES = {
    NotificationType.APPROVAL_REQUESTED: "Freigabe erforderlich",
    NotificationType.CRITICAL_APPROVAL_REQUESTED: "Kritische Freigabe erforderlich",
    NotificationType.REVIEW_REQUIRED: "Prüfung erforderlich",
    NotificationType.REVIEW_OVERDUE: "Überfällig - bitte entscheiden",
    NotificationType.DEFERRED_ITEM_DUE: "Zurückgestellter Eintrag ist fällig",
    NotificationType.APPROVAL_EXPIRING: "Freigabe läuft bald ab",
    NotificationType.APPROVAL_EXPIRED: "Freigabe abgelaufen",
    NotificationType.DECISION_RECORDED: "Entscheidung erfasst",
}


def _message_for(ntype: NotificationType, title: str) -> str:
    prefix = _MESSAGES.get(ntype, "Hinweis")
    return f"{prefix}: {title}" if title else prefix
