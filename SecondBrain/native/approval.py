from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping
from uuid import uuid4
import os
import shutil
import time

from secondbrain.events.domain_events import sanitize_metadata

DEFAULT_LEASE_SECONDS = 300
_LOCK_ACQUIRE_TIMEOUT = 10.0
_LOCK_STALE_SECONDS = 60.0
_IDEMPOTENT_RISK = {"read", "low", "medium"}
_SENSITIVE_PAYLOAD_KEYS = (
    "apikey",
    "authorization",
    "clientsecret",
    "cookie",
    "credential",
    "password",
    "passwd",
    "privatekey",
    "secret",
    "token",
)
_SENSITIVE_WORD = re.compile(
    r"(?i)\b(?:sk-[A-Za-z0-9_-]{8,}|[A-Za-z0-9_-]*(?:secret|token|password|passwd|api[_-]?key|private[_-]?key|credential)[A-Za-z0-9_-]*)\b"
)


def _sanitize_text(value: Any) -> str:
    sanitized = str(sanitize_metadata({"value": "" if value is None else str(value)}).get("value") or "")
    return _SENSITIVE_WORD.sub("***", sanitized)


def _sanitize_payload(value: Any, *, key: str = "") -> Any:
    normalized = "".join(character for character in key.lower() if character.isalnum())
    if key and any(token in normalized for token in _SENSITIVE_PAYLOAD_KEYS):
        return "***"
    if isinstance(value, Mapping):
        return {
            str(item_key): _sanitize_payload(item, key=str(item_key))
            for item_key, item in value.items()
        }
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_sanitize_payload(item) for item in value]
    if isinstance(value, str):
        return _sanitize_text(value)
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return str(value)


class ApprovalConcurrencyError(RuntimeError):
    """Raised on a compare-and-set version conflict (controlled conflict)."""


class ExecutionTokenError(RuntimeError):
    """Raised when an execution is attempted without the valid execution token."""


def _risk_is_idempotent(risk_level: Any) -> bool:
    return str(risk_level or "").strip().lower() in _IDEMPOTENT_RISK


class _FileLock:
    """Portable advisory lock via O_CREAT|O_EXCL with stale-lock recovery.

    Works across processes on POSIX and Windows without fcntl/msvcrt. A lock
    older than the stale threshold is assumed to belong to a crashed process and
    is reclaimed, so a crash never blocks the queue forever.
    """

    def __init__(self, target: Path, *, timeout: float = _LOCK_ACQUIRE_TIMEOUT) -> None:
        self.path = target.with_name(target.name + ".lock")
        self.timeout = timeout
        self._fd: int | None = None

    def __enter__(self) -> "_FileLock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        deadline = time.monotonic() + self.timeout
        while True:
            try:
                self._fd = os.open(str(self.path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(self._fd, str(os.getpid()).encode("ascii", "replace"))
                return self
            except FileExistsError:
                if self._reclaim_if_stale():
                    continue
                if time.monotonic() >= deadline:
                    raise ApprovalConcurrencyError(f"approval_lock_timeout:{self.path.name}")
                time.sleep(0.02)

    def _reclaim_if_stale(self) -> bool:
        try:
            age = time.time() - self.path.stat().st_mtime
        except OSError:
            return False
        if age > _LOCK_STALE_SECONDS:
            try:
                self.path.unlink()
            except OSError:
                return False
            return True
        return False

    def __exit__(self, *exc: Any) -> None:
        if self._fd is not None:
            try:
                os.close(self._fd)
            finally:
                self._fd = None
        try:
            self.path.unlink()
        except OSError:
            pass


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
    "approved": frozenset({"executed", "executing", "expired", "recovery_required"}),
    "executing": frozenset({"completed", "executed", "recovery_required", "failed"}),
    "recovery_required": frozenset({"approved", "executing", "rejected", "expired"}),
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
    version: int = 0
    idempotency_key: str = ""
    tool_idempotent: bool = False
    execution_token: str = ""
    lease_expires_at: str = ""
    executor_id: str = ""

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
        safe_payload = _sanitize_payload(dict(payload or {}))
        # Only override risk defaults when supplied, preserving legacy values.
        extra: dict[str, Any] = {}
        if risk_level is not None:
            extra["risk_level"] = risk_level
        if reason is not None:
            extra["reason"] = _sanitize_text(reason)
        extra.setdefault("idempotency_key", _stable_id(command, intent, text, target))
        extra.setdefault("tool_idempotent", _risk_is_idempotent(risk_level if risk_level is not None else "write"))
        record = ApprovalRequest(
            schema=APPROVAL_SCHEMA,
            approval_id=approval_id,
            created_at=created_at,
            command=command,
            intent=_sanitize_text(intent),
            text=_sanitize_text(text),
            target=_sanitize_text(target),
            category=category,
            plan_id=plan_id,
            step_id=step_id,
            tool_name=tool_name,
            payload=safe_payload if isinstance(safe_payload, dict) else {},
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
        expected_version: int | None = None,
    ) -> dict[str, Any] | None:
        actor = actor.strip()
        if not actor:
            raise ValueError("approval_actor_required")
        new_status = new_status.strip().lower()
        safe_note = _sanitize_text(note)
        # Optimistic concurrency: read first (no exclusive lock), then commit
        # under a short write lock that re-checks the version (compare-and-set).
        # This lets concurrent readers observe the same baseline while still
        # guaranteeing only one writer wins for a given version.
        snapshot = self._read_all()
        baseline_row = next((row for row in snapshot if row.get("approval_id") == approval_id), None)
        if baseline_row is None:
            return None
        read_version = int(baseline_row.get("version") or 0)
        baseline = int(expected_version) if expected_version is not None else read_version
        with _FileLock(self.path):
            rows = self._read_raw()
            updated: dict[str, Any] | None = None
            for row in rows:
                if row.get("approval_id") == approval_id:
                    old_status = str(row.get("status") or "pending").strip().lower()
                    current_version = int(row.get("version") or 0)
                    if baseline != current_version:
                        raise ApprovalConcurrencyError(
                            f"approval_version_conflict:{approval_id}:{baseline}!={current_version}"
                        )
                    allowed = _VALID_APPROVAL_TRANSITIONS.get(old_status, frozenset())
                    if new_status not in allowed:
                        raise ValueError(f"invalid_approval_transition:{old_status}->{new_status}")
                    timestamp = _utc_now()
                    event = {
                        "approval_id": approval_id,
                        "old_status": old_status,
                        "new_status": new_status,
                        "actor": actor,
                        "note": safe_note,
                        "timestamp": timestamp,
                        "plan_id": str(row.get("plan_id") or ""),
                        "step_id": str(row.get("step_id") or ""),
                        "tool_name": str(row.get("tool_name") or row.get("command") or ""),
                    }
                    history = row.get("decision_audit")
                    if not isinstance(history, list):
                        history = []
                    row["status"] = new_status
                    row["decision_note"] = safe_note
                    row["decided_by"] = actor
                    row["decided_at"] = timestamp
                    if new_status == "deferred":
                        row["deferred_until"] = deferred_until
                    if step_state:
                        row["step_state"] = step_state
                    row["version"] = current_version + 1
                    row["decision_audit"] = [*history, event]
                    updated = row
                    break
            if updated is None:
                return None
            self._write_all(rows)
            return dict(updated)

    def begin_execution(
        self,
        approval_id: str,
        *,
        executor_id: str,
        lease_seconds: int = DEFAULT_LEASE_SECONDS,
        expected_version: int | None = None,
        idempotency_key: str = "",
    ) -> dict[str, Any]:
        """Atomically claim an approved item for execution (approved -> executing).

        Returns the row including a single-use ``execution_token``. Only the
        holder of that token may complete the execution. A recovery_required item
        may be resumed only when its tool is idempotent.
        """

        executor_id = executor_id.strip() or "executor"
        with _FileLock(self.path):
            rows = self._read_all()
            for row in rows:
                if row.get("approval_id") != approval_id:
                    continue
                old_status = str(row.get("status") or "").strip().lower()
                current_version = int(row.get("version") or 0)
                if expected_version is not None and int(expected_version) != current_version:
                    raise ApprovalConcurrencyError(
                        f"approval_version_conflict:{approval_id}:{expected_version}!={current_version}"
                    )
                if old_status not in {"approved", "recovery_required"}:
                    raise ApprovalConcurrencyError(f"approval_not_executable:{approval_id}:{old_status}")
                if old_status == "recovery_required" and not bool(row.get("tool_idempotent")):
                    raise ExecutionTokenError(f"manual_review_required:{approval_id}")
                token = uuid4().hex
                timestamp = _utc_now()
                lease = (datetime.now(timezone.utc) + timedelta(seconds=max(1, int(lease_seconds)))).isoformat(timespec="seconds")
                history = row.get("decision_audit")
                if not isinstance(history, list):
                    history = []
                row["status"] = "executing"
                row["execution_token"] = token
                row["executor_id"] = executor_id
                row["lease_expires_at"] = lease
                if idempotency_key:
                    row["idempotency_key"] = idempotency_key
                row["version"] = current_version + 1
                row["decision_audit"] = [
                    *history,
                    {
                        "approval_id": approval_id,
                        "old_status": old_status,
                        "new_status": "executing",
                        "actor": executor_id,
                        "note": "execution_lease_acquired",
                        "timestamp": timestamp,
                    },
                ]
                self._write_all(rows)
                return dict(row)
        raise KeyError(f"approval_not_found:{approval_id}")

    def complete_execution(
        self,
        approval_id: str,
        *,
        execution_token: str,
        expected_version: int | None = None,
        result_status: str = "completed",
    ) -> dict[str, Any]:
        result_status = result_status if result_status in {"completed", "executed", "failed"} else "completed"
        with _FileLock(self.path):
            rows = self._read_all()
            for row in rows:
                if row.get("approval_id") != approval_id:
                    continue
                if str(row.get("status") or "") != "executing":
                    raise ExecutionTokenError(f"approval_not_executing:{approval_id}:{row.get('status')}")
                if str(row.get("execution_token") or "") != execution_token:
                    raise ExecutionTokenError(f"execution_token_mismatch:{approval_id}")
                current_version = int(row.get("version") or 0)
                if expected_version is not None and int(expected_version) != current_version:
                    raise ApprovalConcurrencyError(
                        f"approval_version_conflict:{approval_id}:{expected_version}!={current_version}"
                    )
                timestamp = _utc_now()
                history = row.get("decision_audit")
                if not isinstance(history, list):
                    history = []
                row["status"] = result_status
                row["execution_token"] = ""
                row["lease_expires_at"] = ""
                row["version"] = current_version + 1
                row["decision_audit"] = [
                    *history,
                    {
                        "approval_id": approval_id,
                        "old_status": "executing",
                        "new_status": result_status,
                        "actor": str(row.get("executor_id") or "executor"),
                        "note": "execution_completed",
                        "timestamp": timestamp,
                    },
                ]
                self._write_all(rows)
                return dict(row)
        raise KeyError(f"approval_not_found:{approval_id}")

    def recover_stale_leases(self, *, now: datetime | None = None) -> list[dict[str, Any]]:
        """Mark executions whose lease expired as recovery_required (crash recovery)."""

        moment = now or datetime.now(timezone.utc)
        recovered: list[dict[str, Any]] = []
        with _FileLock(self.path):
            rows = self._read_all()
            changed = False
            for row in rows:
                if str(row.get("status") or "") != "executing":
                    continue
                expiry = self._parse_lease(row.get("lease_expires_at"))
                if expiry is not None and moment < expiry:
                    continue
                history = row.get("decision_audit")
                if not isinstance(history, list):
                    history = []
                row["status"] = "recovery_required"
                row["execution_token"] = ""
                row["version"] = int(row.get("version") or 0) + 1
                row["decision_audit"] = [
                    *history,
                    {
                        "approval_id": str(row.get("approval_id") or ""),
                        "old_status": "executing",
                        "new_status": "recovery_required",
                        "actor": "recovery",
                        "note": "stale_execution_lease",
                        "timestamp": _utc_now(),
                    },
                ]
                recovered.append(dict(row))
                changed = True
            if changed:
                self._write_all(rows)
        return recovered

    @staticmethod
    def _parse_lease(value: Any) -> datetime | None:
        text = str(value or "").strip()
        if not text:
            return None
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed

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
        rows = self._read_raw()
        if any(row.get("status") == "invalid_json" for row in rows) and self._backup_path().exists():
            if self.restore_from_backup():
                rows = self._read_raw()
        return rows

    def _read_raw(self) -> list[dict[str, Any]]:
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

    def _backup_path(self) -> Path:
        return self.path.with_name(self.path.name + ".bak")

    def restore_from_backup(self) -> bool:
        backup = self._backup_path()
        if not backup.exists():
            return False
        try:
            shutil.copy2(backup, self.path)
        except OSError:
            return False
        return True

    def _write_all(self, rows: Iterable[dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            try:
                shutil.copy2(self.path, self._backup_path())
            except OSError:
                pass
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
        normalized.setdefault("version", 0)
        normalized.setdefault("idempotency_key", "")
        normalized.setdefault("tool_idempotent", False)
        normalized.setdefault("execution_token", "")
        normalized.setdefault("lease_expires_at", "")
        normalized.setdefault("executor_id", "")
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
        safe_note = _sanitize_text(note)
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
                "note": safe_note,
                "timestamp": timestamp,
            }
            history = row.get("decision_audit")
            if not isinstance(history, list):
                history = []
            row["status"] = new_status
            row["decision_note"] = safe_note
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
