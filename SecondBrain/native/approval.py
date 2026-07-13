from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from uuid import uuid4

AUDIT_SCHEMA = "secondbrain.native.action_audit.v30_28"
APPROVAL_SCHEMA = "secondbrain.native.approval_queue.v30_28"
REVIEW_SCHEMA = "secondbrain.native.review_queue.v1"

REVIEW_CATEGORIES = frozenset(
    {
        "low_confidence_classification",
        "sensitive_document",
        "failed_import",
        "risky_agent_action",
        "connector_permission_change",
        "delete_request",
    }
)

_VALID_APPROVAL_TRANSITIONS: dict[str, frozenset[str]] = {
    "pending": frozenset({"approved", "rejected", "deferred", "expired", "executed"}),
    "deferred": frozenset({"approved", "rejected"}),
    "approved": frozenset({"executed"}),
}

_VALID_REVIEW_TRANSITIONS: dict[str, frozenset[str]] = {
    "pending": frozenset({"approved", "rejected", "deferred"}),
    "deferred": frozenset({"approved", "rejected"}),
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _runtime_native(root: str | Path) -> Path:
    return Path(root).resolve() / "runtime" / "native"


def audit_path(root: str | Path) -> Path:
    return _runtime_native(root) / "action_audit.jsonl"


def approval_path(root: str | Path) -> Path:
    return _runtime_native(root) / "approval_queue.jsonl"


def review_path(root: str | Path) -> Path:
    return _runtime_native(root) / "review_queue.jsonl"


def _stable_id(*parts: str) -> str:
    raw = "|".join(parts).encode("utf-8", errors="replace")
    return hashlib.sha256(raw).hexdigest()[:16]


@dataclass(frozen=True, slots=True)
class ActionAuditRecord:
    schema: str
    id: str
    timestamp: str
    command: str
    intent: str
    text: str
    status: str
    ok: bool
    requires_confirmation: bool
    confirmed: bool
    dry_run: bool
    executed: bool
    returncode: int | None = None
    target: str = ""
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ApprovalRequest:
    schema: str
    approval_id: str
    created_at: str
    command: str
    intent: str
    text: str
    target: str = ""
    status: str = "pending"
    risk_level: str = "write"
    reason: str = "Schreibende Aktion erfordert explizite Bestätigung."
    category: str = "risky_agent_action"
    deferred_until: str = ""
    decision_note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ApprovalItem:
    schema: str
    approval_id: str
    created_at: str
    command: str
    intent: str
    text: str
    target: str = ""
    status: str = "pending"
    risk_level: str = "write"
    reason: str = "Schreibende Aktion erfordert explizite Bestätigung."
    category: str = "risky_agent_action"
    deferred_until: str = ""
    decision_note: str = ""

    category: str = "risky_agent_action"
    plan_id: str = ""
    step_id: str = ""
    tool_name: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    workspace_id: str | None = None
    step_state: str = ""
    decision_note: str = ""
    decided_by: str = ""
    decided_at: str = ""
    deferred_until: str = ""
    decision_audit: list[dict[str, Any]] = field(default_factory=list)
    review_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# Canonical agent-facing name; ApprovalRequest remains for public compatibility.
ApprovalItem = ApprovalRequest


@dataclass(frozen=True, slots=True)
class ReviewItem:
    schema: str
    review_id: str
    created_at: str
    category: str
    status: str = "pending"
    title: str = ""
    description: str = ""
    source: str = ""
    target: str = ""
    approval_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    decision_note: str = ""
    decided_by: str = ""
    decided_at: str = ""
    deferred_until: str = ""
    decision_audit: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ReviewItem:
    schema: str
    review_id: str
    created_at: str
    category: str
    status: str = "pending"
    title: str = ""
    description: str = ""
    source: str = ""
    target: str = ""
    approval_id: str = ""
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _normalize_category(category: str | None, *, command: str = "", risk_level: str = "") -> str:
    value = (category or "").strip().lower()
    if value in REVIEW_CATEGORIES:
        return value
    cmd = (command or "").strip().lower()
    lvl = (risk_level or "").strip().lower()
    if "delete" in cmd or lvl == "destructive":
        return "delete_request"
    if "permission" in cmd or "role" in cmd:
        return "connector_permission_change"
    if "import" in cmd:
        return "failed_import"
    if "classif" in cmd or "confidence" in cmd:
        return "low_confidence_classification"
    if "sensitive" in cmd or "pii" in cmd:
        return "sensitive_document"
    return "risky_agent_action"


class NativeActionAuditLog:
    def __init__(self, project_root: str | Path):
        self.project_root = Path(project_root).resolve()
        self.path = audit_path(self.project_root)

    def append(self, payload: dict[str, Any], *, confirmed: bool = False, dry_run: bool = False) -> dict[str, Any]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        timestamp = _utc_now()
        record = ActionAuditRecord(
            schema=AUDIT_SCHEMA,
            id=_stable_id(timestamp, str(payload.get("command", "")), str(payload.get("text", "")), str(payload.get("status", ""))),
            timestamp=timestamp,
            command=str(payload.get("command", "")),
            intent=str(payload.get("intent", "")),
            text=str(payload.get("text", "")),
            status=str(payload.get("status", "")),
            ok=bool(payload.get("ok", False)),
            requires_confirmation=bool(payload.get("requires_confirmation", False)),
            confirmed=bool(confirmed),
            dry_run=bool(dry_run),
            executed=bool(payload.get("executed", False)),
            returncode=payload.get("returncode") if isinstance(payload.get("returncode"), int) else None,
            target=str(payload.get("target", "")),
            error=str(payload.get("error", "")),
        ).to_dict()
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        return record

    def latest(self, limit: int = 20) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        rows = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                rows.append({"schema": AUDIT_SCHEMA, "status": "invalid_json", "raw": line})
        return list(reversed(rows[-max(1, int(limit)):]))


class NativeApprovalQueue:
    def __init__(self, project_root: str | Path):
        self.project_root = Path(project_root).resolve()
        self.path = approval_path(self.project_root)

    def create(
        self,
        *,
        command: str,
        intent: str,
        text: str,
        target: str = "",
        risk_level: str | None = None,
        reason: str | None = None,
        category: str = "risky_agent_action",
        plan_id: str = "",
        step_id: str = "",
        tool_name: str = "",
        payload: dict[str, Any] | None = None,
        workspace_id: str | None = None,
        step_state: str = "",
        review_id: str = "",
    ) -> dict[str, Any]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        created_at = _utc_now()
        approval_id = _stable_id(command, intent, text, target, created_at)
        # Only override risk defaults when supplied, preserving legacy values.
        extra: dict[str, Any] = {}
        if risk_level is not None:
            extra["risk_level"] = risk_level
        if reason is not None:
            extra["reason"] = reason
        resolved_risk = str(extra.get("risk_level", "write"))
        extra["category"] = _normalize_category(category, command=command, risk_level=resolved_risk)
        record = ApprovalRequest(
            schema=APPROVAL_SCHEMA,
            approval_id=approval_id,
            created_at=created_at,
            command=command,
            intent=intent,
            text=text,
            target=target,
            category=category,
            plan_id=plan_id,
            step_id=step_id,
            tool_name=tool_name,
            payload=dict(payload or {}),
            workspace_id=workspace_id,
            step_state=step_state,
            review_id=review_id,
            **extra,
        ).to_dict()
        rows = self._read_all()
        rows.append(record)
        self._write_all(rows)
        return record

    def list(self, *, status: str | None = None) -> list[dict[str, Any]]:
        rows = self._read_all()
        if status:
            rows = [row for row in rows if row.get("status") == status]
        return rows

    def get(self, approval_id: str) -> dict[str, Any] | None:
        for row in self._read_all():
            if row.get("approval_id") == approval_id:
                return row
        return None

    def transition(
        self,
        approval_id: str,
        new_status: str,
        *,
        actor: str,
        note: str = "",
        deferred_until: str = "",
        step_state: str = "",
    ) -> dict[str, Any] | None:
        actor = actor.strip()
        if not actor:
            raise ValueError("approval_actor_required")
        new_status = new_status.strip().lower()
        rows = self._read_all()
        updated: dict[str, Any] | None = None
        for row in rows:
            if row.get("approval_id") == approval_id:
                old_status = str(row.get("status") or "pending").strip().lower()
                allowed = _VALID_APPROVAL_TRANSITIONS.get(old_status, frozenset())
                if new_status not in allowed:
                    raise ValueError(f"invalid_approval_transition:{old_status}->{new_status}")
                timestamp = _utc_now()
                event = {
                    "approval_id": approval_id,
                    "old_status": old_status,
                    "new_status": new_status,
                    "actor": actor,
                    "note": note,
                    "timestamp": timestamp,
                    "plan_id": str(row.get("plan_id") or ""),
                    "step_id": str(row.get("step_id") or ""),
                    "tool_name": str(row.get("tool_name") or row.get("command") or ""),
                }
                history = row.get("decision_audit")
                if not isinstance(history, list):
                    history = []
                row["status"] = new_status
                row["decision_note"] = note
                row["decided_by"] = actor
                row["decided_at"] = timestamp
                if new_status == "deferred":
                    row["deferred_until"] = deferred_until
                if step_state:
                    row["step_state"] = step_state
                row["decision_audit"] = [*history, event]
                updated = row
                break
        if updated is None:
            return None
        self._write_all(rows)
        return updated

    def mark(
        self,
        approval_id: str,
        status: str,
        *,
        actor: str = "system",
        note: str = "",
    ) -> dict[str, Any] | None:
        """Backward-compatible, audited wrapper around transition()."""

        return self.transition(approval_id, status, actor=actor, note=note)

    def link_review(self, approval_id: str, review_id: str) -> dict[str, Any]:
        rows = self._read_all()
        for row in rows:
            if row.get("approval_id") == approval_id:
                row["review_id"] = review_id
                self._write_all(rows)
                return row
        raise KeyError(f"approval_not_found:{approval_id}")

    def _read_all(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        rows: list[dict[str, Any]] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                value = json.loads(line)
                if isinstance(value, dict):
                    rows.append(self._with_decision_defaults(value))
            except json.JSONDecodeError:
                rows.append({"schema": APPROVAL_SCHEMA, "status": "invalid_json", "raw": line})
        return rows

    def _write_all(self, rows: Iterable[dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_name(f"{self.path.name}.{uuid4().hex}.tmp")
        try:
            with temporary.open("w", encoding="utf-8") as fh:
                for row in rows:
                    fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            temporary.replace(self.path)
        finally:
            temporary.unlink(missing_ok=True)

    @staticmethod
    def _with_decision_defaults(row: dict[str, Any]) -> dict[str, Any]:
        if "approval_id" not in row:
            return row
        normalized = dict(row)
        normalized.setdefault("status", "pending")
        normalized.setdefault("decision_note", "")
        normalized.setdefault("decided_by", "")
        normalized.setdefault("decided_at", "")
        normalized.setdefault("deferred_until", "")
        normalized.setdefault("decision_audit", [])
        normalized.setdefault("step_state", "")
        normalized.setdefault("review_id", "")
        return normalized


class ReviewQueue:
    def __init__(self, project_root: str | Path):
        self.project_root = Path(project_root).resolve()
        self.path = review_path(self.project_root)

    def create(
        self,
        *,
        category: str,
        title: str,
        description: str = "",
        source: str = "",
        target: str = "",
        approval_id: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        category = category.strip().lower()
        if category not in REVIEW_CATEGORIES:
            raise ValueError(f"invalid_review_category:{category}")
        created_at = _utc_now()
        review_id = _stable_id(category, title, source, target, approval_id, created_at)
        record = ReviewItem(
            schema=REVIEW_SCHEMA,
            review_id=review_id,
            created_at=created_at,
            category=category,
            title=title,
            description=description,
            source=source,
            target=target,
            approval_id=approval_id,
            metadata=dict(metadata or {}),
        ).to_dict()
        rows = self._read_all()
        rows.append(record)
        self._write_all(rows)
        return record

    def list(self, *, status: str | None = None, category: str | None = None) -> list[dict[str, Any]]:
        rows = self._read_all()
        if status:
            rows = [row for row in rows if row.get("status") == status]
        if category:
            rows = [row for row in rows if row.get("category") == category]
        return rows

    def get(self, review_id: str) -> dict[str, Any] | None:
        for row in self._read_all():
            if row.get("review_id") == review_id:
                return row
        return None

    def transition(
        self,
        review_id: str,
        new_status: str,
        *,
        actor: str,
        note: str = "",
        deferred_until: str = "",
    ) -> dict[str, Any] | None:
        actor = actor.strip()
        if not actor:
            raise ValueError("review_actor_required")
        new_status = new_status.strip().lower()
        rows = self._read_all()
        for row in rows:
            if row.get("review_id") != review_id:
                continue
            old_status = str(row.get("status") or "pending").strip().lower()
            if new_status not in _VALID_REVIEW_TRANSITIONS.get(old_status, frozenset()):
                raise ValueError(f"invalid_review_transition:{old_status}->{new_status}")
            timestamp = _utc_now()
            event = {
                "review_id": review_id,
                "approval_id": str(row.get("approval_id") or ""),
                "old_status": old_status,
                "new_status": new_status,
                "actor": actor,
                "note": note,
                "timestamp": timestamp,
            }
            history = row.get("decision_audit")
            if not isinstance(history, list):
                history = []
            row["status"] = new_status
            row["decision_note"] = note
            row["decided_by"] = actor
            row["decided_at"] = timestamp
            if new_status == "deferred":
                row["deferred_until"] = deferred_until
            row["decision_audit"] = [*history, event]
            self._write_all(rows)
            return row
        return None

    def _read_all(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        rows = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                rows.append({"schema": REVIEW_SCHEMA, "status": "invalid_json", "raw": line})
                continue
            if isinstance(value, dict):
                rows.append(self._with_decision_defaults(value))
        return rows

    def _write_all(self, rows: Iterable[dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_name(f"{self.path.name}.{uuid4().hex}.tmp")
        try:
            with temporary.open("w", encoding="utf-8") as handle:
                for row in rows:
                    handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            temporary.replace(self.path)
        finally:
            temporary.unlink(missing_ok=True)

    @staticmethod
    def _with_decision_defaults(row: dict[str, Any]) -> dict[str, Any]:
        if "review_id" not in row:
            return row
        normalized = dict(row)
        normalized.setdefault("status", "pending")
        normalized.setdefault("approval_id", "")
        normalized.setdefault("metadata", {})
        normalized.setdefault("decision_note", "")
        normalized.setdefault("decided_by", "")
        normalized.setdefault("decided_at", "")
        normalized.setdefault("deferred_until", "")
        normalized.setdefault("decision_audit", [])
        return normalized


class ReviewQueue:
    def __init__(self, project_root: str | Path):
        self.project_root = Path(project_root).resolve()
        self.path = review_path(self.project_root)

    def create(
        self,
        *,
        category: str,
        title: str,
        description: str = "",
        source: str = "",
        target: str = "",
        approval_id: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        created_at = _utc_now()
        cat = _normalize_category(category)
        review_id = _stable_id(cat, title, source, target, created_at)
        record = ReviewItem(
            schema=REVIEW_SCHEMA,
            review_id=review_id,
            created_at=created_at,
            category=cat,
            title=title,
            description=description,
            source=source,
            target=target,
            approval_id=approval_id,
            metadata=metadata or {},
        ).to_dict()
        rows = self._read_all()
        rows.append(record)
        self._write_all(rows)
        return record

    def list(self, *, status: str | None = None, category: str | None = None) -> list[dict[str, Any]]:
        rows = self._read_all()
        if status:
            rows = [row for row in rows if row.get("status") == status]
        if category:
            cat = _normalize_category(category)
            rows = [row for row in rows if row.get("category") == cat]
        return rows

    def mark(self, review_id: str, status: str, *, note: str = "") -> dict[str, Any] | None:
        rows = self._read_all()
        updated: dict[str, Any] | None = None
        for row in rows:
            if row.get("review_id") == review_id:
                row["status"] = status
                row["decision_note"] = note
                row["updated_at"] = _utc_now()
                updated = row
        self._write_all(rows)
        return updated

    def _read_all(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        rows: list[dict[str, Any]] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                value = json.loads(line)
                if isinstance(value, dict):
                    rows.append(value)
            except json.JSONDecodeError:
                rows.append({"schema": REVIEW_SCHEMA, "status": "invalid_json", "raw": line})
        return rows

    def _write_all(self, rows: Iterable[dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def native_audit_status(project_root: str | Path, *, limit: int = 20) -> dict[str, Any]:
    root = Path(project_root).resolve()
    audit = NativeActionAuditLog(root)
    queue = NativeApprovalQueue(root)
    pending = queue.list(status="pending")
    latest = audit.latest(limit=limit)
    return {
        "ok": True,
        "schema": "secondbrain.native.audit_status.v30_28",
        "project_root": str(root),
        "audit_path": str(audit.path),
        "approval_path": str(queue.path),
        "audit_count_visible": len(latest),
        "pending_approvals": len(pending),
        "latest": latest,
        "approvals": pending,
    }
