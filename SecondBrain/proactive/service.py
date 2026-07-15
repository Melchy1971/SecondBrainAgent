"""Proactive suggestion engine.

Detects relevant situations from already-fetched context and proposes actions -
it never executes them. Every suggestion carries evidence and a confidence, and
low confidence is never rendered as critical. Duplicates are collapsed on a
stable dedup key; dismissed suggestions stay suppressed for a cooldown and
lower that category's future priority; snoozed ones stay hidden until their
time. Accepting a suggestion only yields a task/plan intent, and any external
effect within that intent is marked approval-required. Feedback is auditable.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Any, Mapping, Sequence
from uuid import uuid4

from secondbrain.proactive.models import (
    FeedbackRecord, Priority, Suggestion, SuggestionCategory, SuggestionStatus,
)

__all__ = ["ProactiveEngine", "redact_suggestion_text", "DEFAULT_COOLDOWN_DAYS"]

DEFAULT_COOLDOWN_DAYS = 7
_SECRET_PATTERNS = (
    re.compile(r"-----BEGIN(?: [A-Z0-9]+)? PRIVATE KEY-----[\s\S]*", re.IGNORECASE),
    re.compile(r"(?i)[\w.\-]*(?:api[\s_-]?key|apikey|token|secret|password|passwd|credential(?:s)?)\s*[:=]\s*[^\s,;\"']+"),
    re.compile(r"sk-[A-Za-z0-9_-]{12,}"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
)


def redact_suggestion_text(text: str) -> str:
    out = text or ""
    for pattern in _SECRET_PATTERNS:
        out = pattern.sub("[REDACTED]", out)
    return out


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat(timespec="seconds")


def _parse(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt


def _priority_for(confidence: float) -> str:
    # low confidence is never critical
    if confidence < 0.5:
        return Priority.LOW.value
    if confidence < 0.7:
        return Priority.MEDIUM.value
    if confidence < 0.9:
        return Priority.HIGH.value
    return Priority.CRITICAL.value


class ProactiveEngine:
    def __init__(self, *, cooldown_days: int = DEFAULT_COOLDOWN_DAYS,
                 task_factory: Any | None = None, plan_factory: Any | None = None) -> None:
        self.cooldown_days = cooldown_days
        self.disabled_rules: set[tuple[str, str]] = set()
        self.task_factory, self.plan_factory = task_factory, plan_factory
        self._suggestions: dict[str, Suggestion] = {}
        self._by_key: dict[str, str] = {}          # dedup_key -> suggestion_id
        self._dismissed_until: dict[str, datetime] = {}
        self._snoozed_until: dict[str, datetime] = {}
        self._dismiss_count: dict[str, int] = {}   # category -> count (priority damping)
        self._feedback: list[FeedbackRecord] = []

    # -- generation -------------------------------------------------------

    def generate(self, *, workspace_id: str, context: Mapping[str, Any], now: datetime | None = None) -> list[Suggestion]:
        moment = now or _now()
        out: list[Suggestion] = []
        for cat, cand in self._candidates(workspace_id, context, moment):
            if (workspace_id, cat) in self.disabled_rules or ("*", cat) in self.disabled_rules:
                continue
            if sum(s.workspace_id == workspace_id and s.category == cat and s.status == SuggestionStatus.NEW.value
                   for s in self._suggestions.values()) >= 3:
                continue
            key = self._key(workspace_id, cat, cand["subject"])
            # suppression: cooldown after dismiss, or active snooze
            if key in self._dismissed_until and moment < self._dismissed_until[key]:
                continue
            if key in self._snoozed_until and moment < self._snoozed_until[key]:
                continue
            if key in self._by_key:  # dedup - already present
                continue
            confidence = float(cand["confidence"])
            priority = _priority_for(confidence)
            # dismiss history dampens priority (never raise, only lower)
            if self._dismiss_count.get(cat, 0) >= 2 and priority == Priority.CRITICAL.value:
                priority = Priority.HIGH.value
            sug = Suggestion(
                suggestion_id=str(uuid4()), workspace_id=workspace_id, category=cat,
                title=redact_suggestion_text(cand["title"]),
                description=redact_suggestion_text(cand.get("description", "")),
                evidence=[self._redact_evidence(e) for e in cand.get("evidence", [])],
                confidence=confidence, priority=priority,
                proposed_action=cand.get("proposed_action", {}),
                expires_at=cand.get("expires_at", ""), created_at=_iso(moment), dedup_key=key,
                source_references=sorted({str(e.get("source_id")) for e in cand.get("evidence", []) if e.get("source_id")}),
                rule_id=cat,
            )
            self._suggestions[sug.suggestion_id] = sug
            self._by_key[key] = sug.suggestion_id
            out.append(sug)
        out.sort(key=lambda s: (-_PRIO_WEIGHT[s.priority], -s.confidence))
        return out

    def _candidates(self, workspace_id: str, context: Mapping[str, Any], moment: datetime):
        cands: list[tuple[str, dict[str, Any]]] = []
        soon = moment + timedelta(days=3)
        for t in context.get("tasks", []) or []:
            due = _parse(t.get("due"))
            if due is not None and due <= soon and not t.get("started"):
                cands.append((SuggestionCategory.DEADLINE_RISK.value, {
                    "subject": t.get("id", t.get("title", "")), "confidence": 0.85,
                    "title": f"Frist bald: {t.get('title','')}",
                    "description": f"Fällig {t.get('due')}, noch nicht begonnen.",
                    "evidence": [{"source_id": t.get("id", ""), "due": t.get("due")}],
                    "proposed_action": {"type": "task", "title": f"Starten: {t.get('title','')}",
                                        "external": False}}))
        for e in context.get("events", []) or []:
            if not e.get("preparation"):
                cands.append((SuggestionCategory.MISSING_PREPARATION.value, {
                    "subject": e.get("id", ""), "confidence": 0.6,
                    "title": f"Vorbereitung fehlt: {e.get('title','')}",
                    "evidence": [{"source_id": e.get("id", "")}],
                    "proposed_action": {"type": "task", "title": f"Vorbereiten: {e.get('title','')}",
                                        "external": False}}))
        for m in context.get("mail", []) or []:
            if m.get("awaiting_reply"):
                cands.append((SuggestionCategory.UNANSWERED_MESSAGE.value, {
                    "subject": m.get("id", ""), "confidence": 0.7,
                    "title": f"Unbeantwortet: {m.get('subject','')}",
                    "evidence": [{"source_id": m.get("id", "")}],
                    "proposed_action": {"type": "task", "title": "Antwort entwerfen",
                                        "external": True, "approval_required": True}}))
        for p in context.get("projects", []) or []:
            if p.get("blocked_days", 0) >= p.get("blocked_threshold", 7):
                cands.append((SuggestionCategory.BLOCKED_PROJECT.value, {
                    "subject": p.get("id", ""), "confidence": 0.75,
                    "title": f"Projekt blockiert: {p.get('name','')}",
                    "evidence": [{"source_id": p.get("id", ""), "blocked_days": p.get("blocked_days")}],
                    "proposed_action": {"type": "task", "title": "Blocker klären", "external": False}}))
        for c in context.get("contracts", []) or []:
            exp = _parse(c.get("expires"))
            if exp is not None and exp <= moment + timedelta(days=30):
                cands.append((SuggestionCategory.CONTRACT_EXPIRY.value, {
                    "subject": c.get("id", ""), "confidence": 0.8,
                    "title": f"Vertrag läuft ab: {c.get('name','')}",
                    "evidence": [{"source_id": c.get("id", ""), "expires": c.get("expires")}],
                    "proposed_action": {"type": "task", "title": "Verlängerung prüfen", "external": False}}))
        for conn in context.get("connectors", []) or []:
            if conn.get("error_count", 0) >= 3:
                cands.append((SuggestionCategory.CONNECTOR_PROBLEM.value, {
                    "subject": conn.get("name", ""), "confidence": 0.9,
                    "title": f"Connector fehlerhaft: {conn.get('name','')}",
                    "evidence": [{"connector": conn.get("name", ""), "errors": conn.get("error_count")}],
                    "proposed_action": {"type": "task", "title": "Connector prüfen", "external": False}}))
        backup = context.get("backup", {}) or {}
        last = _parse(backup.get("last_at"))
        if last is not None and last <= moment - timedelta(days=backup.get("max_age_days", 7)):
            cands.append((SuggestionCategory.MISSING_BACKUP.value, {
                "subject": "backup", "confidence": 0.85,
                "title": "Backup überfällig",
                "evidence": [{"last_backup": backup.get("last_at")}],
                "proposed_action": {"type": "job", "title": "Backup starten", "external": False}}))
        for a in context.get("approvals", []) or []:
            due = _parse(a.get("due"))
            if due is not None and due <= moment:
                cands.append((SuggestionCategory.OVERDUE_APPROVAL.value, {
                    "subject": a.get("id", ""), "confidence": 0.8,
                    "title": "Approval überfällig",
                    "evidence": [{"approval_id": a.get("id", ""), "due": a.get("due")}],
                    "proposed_action": {"type": "review", "title": "Approval bearbeiten", "external": False}}))
        for k in context.get("knowledge_conflicts", []) or []:
            cands.append((SuggestionCategory.KNOWLEDGE_CONFLICT.value, {
                "subject": k.get("id", ""), "confidence": 0.55,
                "title": f"Widerspruch: {k.get('subject','')}",
                "evidence": [{"source_id": s} for s in k.get("sources", [])],
                "proposed_action": {"type": "review", "title": "Konflikt lösen", "external": False}}))
        for r in context.get("recurring", []) or []:
            if r.get("occurrences", 0) >= 3:
                cands.append((SuggestionCategory.RECURRING_PATTERN.value, {
                    "subject": r.get("id", ""), "confidence": 0.5,
                    "title": f"Wiederkehrend: {r.get('name','')}",
                    "evidence": [{"pattern": r.get("name", ""), "n": r.get("occurrences")}],
                    "proposed_action": {"type": "automation", "title": "Automatisierung vorschlagen",
                                        "external": False}}))
        for memory in context.get("stale_memories", []) or []:
            cands.append((SuggestionCategory.STALE_MEMORY.value, {
                "subject": memory.get("id", ""), "confidence": 0.7,
                "title": "Memory sollte bestätigt werden", "evidence": [{"source_id": memory.get("id", "")}],
                "proposed_action": {"type": "review", "title": "Memory prüfen", "external": False}}))
        for job in context.get("failed_jobs", []) or []:
            if int(job.get("attempts", 0)) >= 2:
                cands.append((SuggestionCategory.FAILED_JOB.value, {
                    "subject": job.get("id", ""), "confidence": 0.85,
                    "title": "Job wiederholt fehlgeschlagen", "evidence": [{"source_id": job.get("id", "")}],
                    "proposed_action": {"type": "review", "title": "Recovery prüfen", "external": False}}))
        return cands

    # -- user actions -----------------------------------------------------

    def accept(self, suggestion_id: str, *, now: datetime | None = None) -> dict[str, Any]:
        sug = self._suggestions[suggestion_id]
        sug.status = SuggestionStatus.ACCEPTED.value
        self._log(sug, "accepted")
        action = dict(sug.proposed_action)
        # Accepting only creates a task/plan intent. Any external effect stays
        # approval-gated - the engine never performs the external action itself.
        action_type = action.get("type", "task")
        if action_type not in {"task", "plan", "review", "briefing"}:
            action_type = "review"
        created = None
        if action_type == "task" and not action.get("external") and self.task_factory is not None:
            created = self.task_factory(workspace_id=sug.workspace_id, title=action.get("title", sug.title),
                                        source_reference=sug.suggestion_id)
        elif action_type == "plan" and not action.get("external") and self.plan_factory is not None:
            created = self.plan_factory(workspace_id=sug.workspace_id, goal=action.get("title", sug.title))
        intent = {"created": action_type, "created_result": created, "title": action.get("title", sug.title),
                  "external_action": bool(action.get("external")),
                  "approval_required": bool(action.get("external")) or bool(action.get("approval_required")),
                  "executed": False}
        return intent

    def acknowledge(self, suggestion_id: str) -> None:
        sug = self._suggestions[suggestion_id]
        sug.status = SuggestionStatus.ACKNOWLEDGED.value
        self._log(sug, "acknowledged")

    def dismiss(self, suggestion_id: str, *, now: datetime | None = None, cooldown_days: int | None = None) -> None:
        sug = self._suggestions[suggestion_id]
        moment = now or _now()
        cd = self.cooldown_days if cooldown_days is None else cooldown_days
        sug.status = SuggestionStatus.DISMISSED.value
        self._dismissed_until[sug.dedup_key] = moment + timedelta(days=cd)
        self._dismiss_count[sug.category] = self._dismiss_count.get(sug.category, 0) + 1
        self._by_key.pop(sug.dedup_key, None)  # allow future regen after cooldown
        self._log(sug, "dismissed", f"cooldown_until={_iso(self._dismissed_until[sug.dedup_key])}")

    def snooze(self, suggestion_id: str, *, until: datetime, now: datetime | None = None) -> None:
        sug = self._suggestions[suggestion_id]
        sug.status = SuggestionStatus.SNOOZED.value
        sug.snoozed_until = _iso(until)
        self._snoozed_until[sug.dedup_key] = until
        self._by_key.pop(sug.dedup_key, None)
        self._log(sug, "snoozed", f"until={_iso(until)}")

    def disable_rule(self, category: str, *, workspace_id: str = "*") -> None:
        self.disabled_rules.add((workspace_id, category))

    def enable_rule(self, category: str, *, workspace_id: str = "*") -> None:
        self.disabled_rules.discard((workspace_id, category))

    # -- read / audit -----------------------------------------------------

    def active(self, *, workspace_id: str) -> list[Suggestion]:
        return [s for s in self._suggestions.values()
                if s.workspace_id == workspace_id and s.status in
                (SuggestionStatus.NEW.value, SuggestionStatus.ACKNOWLEDGED.value)]

    def feedback_log(self) -> list[FeedbackRecord]:
        return list(self._feedback)

    def notification_preview(self, suggestion: Suggestion) -> str:
        # title only, secret-free; no evidence bodies
        return redact_suggestion_text(f"{suggestion.title} ({suggestion.priority})")

    # -- helpers ----------------------------------------------------------

    @staticmethod
    def _key(workspace_id: str, category: str, subject: str) -> str:
        raw = f"{workspace_id}|{category}|{str(subject).strip().lower()}"
        return sha256(raw.encode("utf-8")).hexdigest()[:24]

    @staticmethod
    def _redact_evidence(evidence: Mapping[str, Any]) -> dict[str, Any]:
        return {k: (redact_suggestion_text(v) if isinstance(v, str) else v) for k, v in evidence.items()}

    def _log(self, sug: Suggestion, action: str, detail: str = "") -> None:
        self._feedback.append(FeedbackRecord(at=_iso(_now()), suggestion_id=sug.suggestion_id,
                                             dedup_key=sug.dedup_key, category=sug.category,
                                             action=action, detail=detail))


_PRIO_WEIGHT = {Priority.CRITICAL.value: 3, Priority.HIGH.value: 2, Priority.MEDIUM.value: 1, Priority.LOW.value: 0}
