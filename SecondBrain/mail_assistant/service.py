"""Mail assistant service.

Analysis functions (summarize, classify, prioritize, extract) require no
approval and never leak secrets - summaries and drafts are redacted. Sending,
forwarding, deleting, label writes and external task creation are never executed
directly: they prepare an approval bound to a payload hash and are committed
exactly once against a connector (offline -> controlled error, no data loss).
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Any, Sequence

from secondbrain.mail_assistant.models import Category, MailMessage, MailThread, PriorityScore

__all__ = ["MailAssistant", "MailConnectorError", "WRITE_ACTIONS", "redact_mail_text"]

WRITE_ACTIONS = ["send_reply", "send_new_message", "forward_message", "archive_message",
                 "delete_message", "change_labels", "create_external_task"]

_SECRET_PATTERNS = (
    re.compile(r"-----BEGIN(?: [A-Z0-9]+)? PRIVATE KEY-----[\s\S]*?-----END(?: [A-Z0-9]+)? PRIVATE KEY-----", re.IGNORECASE),
    re.compile(r"-----BEGIN(?: [A-Z0-9]+)? PRIVATE KEY-----[\s\S]*", re.IGNORECASE),
    re.compile(r"(?i)[\w.\-]*(?:api[\s_-]?key|apikey|access[_-]?token|auth[_-]?token|token|secret|client[_-]?secret|password|passwd|credential(?:s)?)\s*[:=]\s*[^\s,;\"']+"),
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/-]+=*"),
    re.compile(r"sk-[A-Za-z0-9_-]{12,}"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
)
_ESCALATION = ("urgent", "asap", "dringend", "sofort", "deadline", "eskal", "wichtig", "critical", "frist")
_DATE_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2}|\d{1,2}\.\d{1,2}\.\d{2,4})\b")
_ACTION_RE = re.compile(r"(?i)(?:bitte|please|kannst du|could you|können sie|todo|to-do|aufgabe)\b[:,]?\s*(.+)")
_REDACTED = "[REDACTED]"


class MailConnectorError(RuntimeError):
    pass


def redact_mail_text(text: str) -> str:
    out = text or ""
    for pattern in _SECRET_PATTERNS:
        out = pattern.sub(_REDACTED, out)
    return out


class MailAssistant:
    def __init__(self, connector: Any | None = None, *, vips: Sequence[str] | None = None,
                 projects: Sequence[str] | None = None, owner: str = "") -> None:
        self.connector = connector
        self.vips = {v.lower() for v in (vips or [])}
        self.projects = [p.lower() for p in (projects or [])]
        self.owner = owner.lower()
        self._committed: set[str] = set()

    # -- read / analysis --------------------------------------------------

    def list_messages(self, messages: Sequence[MailMessage], *, workspace_id: str, unread_only: bool = False) -> list[MailMessage]:
        out = [m for m in messages if m.workspace_id == workspace_id]
        if unread_only:
            out = [m for m in out if m.unread]
        return sorted(out, key=lambda m: m.received_at)

    def list_threads(self, threads: Sequence[MailThread], *, workspace_id: str) -> list[MailThread]:
        return sorted([t for t in threads if t.workspace_id == workspace_id], key=lambda t: t.latest_message_at, reverse=True)

    def summarize_thread(self, messages: Sequence[MailMessage]) -> dict[str, Any]:
        msgs = sorted(messages, key=lambda m: m.received_at)
        participants = sorted({m.sender for m in msgs} | {r for m in msgs for r in m.recipients})
        bullets = []
        open_questions = []
        for m in msgs:
            body = redact_mail_text(m.body)
            first = re.sub(r"\s+", " ", body).strip()[:180]
            bullets.append(f"{m.sender}: {first}")
            for sentence in re.split(r"(?<=[.?!])\s+", body):
                if sentence.strip().endswith("?"):
                    open_questions.append(redact_mail_text(sentence.strip())[:160])
        return {
            "subject": msgs[0].subject if msgs else "",
            "participants": participants,
            "message_count": len(msgs),
            "summary": " | ".join(bullets)[:1200],
            "open_questions": open_questions[:5],
            "attachments": self.detect_attachments(msgs),
        }

    def classify_message(self, message: MailMessage) -> str:
        text = f"{message.subject} {message.body}".lower()
        if any(w in text for w in ("rechnung", "invoice", "zahlung", "betrag")):
            return Category.INVOICE.value
        if any(w in text for w in ("vertrag", "contract", "nda", "agreement")):
            return Category.CONTRACT.value
        if any(w in text for w in ("meeting", "termin", "call", "besprechung", "einladung")):
            return Category.MEETING.value
        if any(w in text for w in ("unsubscribe", "gewonnen", "lottery", "viagra")):
            return Category.SPAM_CANDIDATE.value
        if any(p in text for p in self.projects):
            return Category.PROJECT.value
        if "?" in text or any(w in text for w in ("bitte", "please", "todo", "aufgabe")):
            return Category.ACTION_REQUIRED.value
        if any(w in text for w in ("warte", "waiting", "follow up", "follow-up")):
            return Category.WAITING_FOR_REPLY.value
        return Category.INFORMATION.value

    def score_message(self, message: MailMessage) -> PriorityScore:
        text = f"{message.subject} {message.body}".lower()
        factors: dict[str, float] = {}
        if message.sender.lower() in self.vips:
            factors["vip"] = 3.0
        if _DATE_RE.search(text) or "frist" in text or "deadline" in text:
            factors["deadline"] = 2.0
        if self.owner and (self.owner in text or self.owner in [r.lower() for r in message.recipients]):
            factors["direct_address"] = 1.5
        if any(w in text for w in _ESCALATION):
            factors["escalation"] = 2.0
        if message.unread:
            factors["unread"] = 1.0
        if any(p in text for p in self.projects):
            factors["project"] = 1.0
        if "?" in text:
            factors["open_question"] = 1.0
        if "?" in text and factors.get("direct_address"):
            factors["reply_expected"] = 1.0
        age_days = self._age_days(message.received_at)
        if age_days >= 3:
            factors["age"] = min(2.0, age_days * 0.2)
        return PriorityScore(score=sum(factors.values()), factors=factors)

    def prioritize_inbox(self, messages: Sequence[MailMessage], *, workspace_id: str) -> list[dict[str, Any]]:
        scored = []
        for m in self.list_messages(messages, workspace_id=workspace_id):
            ps = self.score_message(m)
            scored.append({"subject": m.subject, "sender": m.sender, "category": self.classify_message(m),
                           "unread": m.unread, "source_reference": m.external_id or m.message_id, **ps.to_dict()})
        scored.sort(key=lambda x: -x["score"])
        return scored

    def detect_follow_up(self, messages: Sequence[MailMessage]) -> dict[str, Any]:
        if not messages:
            return {"follow_up": False}
        last = sorted(messages, key=lambda m: m.received_at)[-1]
        waiting = bool(self.owner and last.sender.lower() == self.owner and "?" in last.body)
        awaiting_reply = bool(self.owner and last.sender.lower() != self.owner and "?" in last.body)
        return {"follow_up": waiting or awaiting_reply,
                "reason": "waiting_for_reply" if waiting else ("reply_expected" if awaiting_reply else "")}

    def extract_dates(self, text: str) -> list[str]:
        return _DATE_RE.findall(text or "")

    def detect_attachments(self, messages: Sequence[MailMessage]) -> list[dict[str, str]]:
        refs = []
        for m in messages:
            for name in m.attachments:
                refs.append({"name": name, "message_reference": m.external_id or m.message_id})
        return refs

    def extract_tasks(self, message: MailMessage, *, confidence: float = 0.6) -> list[dict[str, Any]]:
        proposals = []
        body = redact_mail_text(message.body)
        for line in body.splitlines():
            m = _ACTION_RE.search(line)
            if m and m.group(1).strip():
                dates = self.extract_dates(line)
                proposals.append({
                    "candidate_title": m.group(1).strip()[:200],
                    "source_reference": message.external_id or message.message_id,
                    "confidence": confidence,
                    "suggested_due": dates[0] if dates else None,
                    "status": "proposed",  # user confirms or rejects
                })
        return proposals

    def generate_reply_draft(self, messages: Sequence[MailMessage], *, style: str = "sachlich",
                             open_questions: Sequence[str] | None = None) -> dict[str, Any]:
        summary = self.summarize_thread(messages)
        questions = list(open_questions or summary["open_questions"])
        lines = [f"Hallo {self._first_name(messages)},", ""]
        if questions:
            lines.append("zu deinen Punkten:")
            for q in questions:
                lines.append(f"- {redact_mail_text(q)}  [UNSICHER: bitte prüfen]")
        else:
            lines.append("danke für deine Nachricht. [UNSICHER: Antwort ergänzen]")
        lines += ["", "Viele Grüße"]
        return {
            "sent": False,  # a draft is never sent
            "style": style,
            "draft": redact_mail_text("\n".join(lines)),
            "open_questions": questions,
            "attachments": summary["attachments"],
            "disclaimer": "Entwurf enthält keine verbindlichen Zusagen; Unsicherheiten markiert.",
        }

    # -- write with approval ----------------------------------------------

    @staticmethod
    def _payload_hash(payload: dict[str, Any]) -> str:
        return sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()

    def prepare_change(self, action: str, payload: dict[str, Any], *, workspace_id: str,
                       ttl_minutes: int = 30, approval_queue: Any | None = None, now: datetime | None = None) -> dict[str, Any]:
        if action not in WRITE_ACTIONS:
            raise ValueError(f"unknown_write_action:{action}")
        moment = now or datetime.now(timezone.utc)
        bound = {"action": action, "workspace_id": workspace_id,
                 "payload_hash": self._payload_hash(payload),
                 "expires_at": (moment + timedelta(minutes=ttl_minutes)).isoformat(timespec="seconds")}
        approval_id = ""
        if approval_queue is not None:
            try:
                approval = approval_queue.create(
                    command=f"mail.{action}", intent=action, text=f"Mail {action}",
                    target=str(payload.get("thread_id") or payload.get("message_id") or ""),
                    category="external_send", risk_level="high", tool_name=f"mail.{action}",
                    workspace_id=workspace_id, payload=dict(bound))
                approval_id = str(approval.get("approval_id") or "")
            except Exception:  # noqa: BLE001
                approval_id = ""
        return {"status": "approval_required", "approval_id": approval_id, **bound}

    def commit_change(self, prepared: dict[str, Any], payload: dict[str, Any], *, approved: bool,
                      now: datetime | None = None) -> dict[str, Any]:
        moment = now or datetime.now(timezone.utc)
        approval_id = str(prepared.get("approval_id") or prepared.get("payload_hash"))
        if not approved:
            return {"status": "blocked", "reason": "not_approved"}
        if self._payload_hash(payload) != prepared.get("payload_hash"):
            return {"status": "invalid", "reason": "payload_changed"}
        exp = self._parse(prepared.get("expires_at"))
        if exp is not None and moment > exp:
            return {"status": "expired", "reason": "approval_expired"}
        if approval_id in self._committed:
            return {"status": "duplicate", "reason": "already_committed"}
        if self.connector is None:
            return {"status": "no_connector", "reason": "connector_not_configured"}
        method = getattr(self.connector, prepared.get("action", ""), None)
        if method is None:
            return {"status": "unsupported", "reason": prepared.get("action")}
        try:
            result = method(payload)
        except MailConnectorError as exc:
            return {"status": "connector_offline", "reason": str(exc)}
        except Exception as exc:  # noqa: BLE001
            return {"status": "error", "reason": f"{type(exc).__name__}: {exc}"}
        self._committed.add(approval_id)
        return {"status": "committed", "result": result}

    # -- helpers ----------------------------------------------------------

    @staticmethod
    def _parse(value: Any) -> datetime | None:
        text = str(value or "").strip()
        if not text:
            return None
        try:
            dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return None
        return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt

    def _age_days(self, received_at: str) -> float:
        dt = self._parse(received_at)
        if dt is None:
            return 0.0
        return max(0.0, (datetime.now(timezone.utc) - dt).total_seconds() / 86400.0)

    @staticmethod
    def _first_name(messages: Sequence[MailMessage]) -> str:
        if not messages:
            return "zusammen"
        sender = sorted(messages, key=lambda m: m.received_at)[-1].sender
        local = sender.split("@")[0].replace(".", " ").split()
        return local[0].capitalize() if local else "zusammen"
