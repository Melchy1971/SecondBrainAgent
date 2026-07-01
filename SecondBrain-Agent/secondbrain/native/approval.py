from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

AUDIT_SCHEMA = "secondbrain.native.action_audit.v30_28"
APPROVAL_SCHEMA = "secondbrain.native.approval_queue.v30_28"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _runtime_native(root: str | Path) -> Path:
    return Path(root).resolve() / "runtime" / "native"


def audit_path(root: str | Path) -> Path:
    return _runtime_native(root) / "action_audit.jsonl"


def approval_path(root: str | Path) -> Path:
    return _runtime_native(root) / "approval_queue.jsonl"


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

    def create(self, *, command: str, intent: str, text: str, target: str = "") -> dict[str, Any]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        created_at = _utc_now()
        approval_id = _stable_id(command, intent, text, target, created_at)
        record = ApprovalRequest(
            schema=APPROVAL_SCHEMA,
            approval_id=approval_id,
            created_at=created_at,
            command=command,
            intent=intent,
            text=text,
            target=target,
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

    def mark(self, approval_id: str, status: str) -> dict[str, Any] | None:
        rows = self._read_all()
        updated: dict[str, Any] | None = None
        for row in rows:
            if row.get("approval_id") == approval_id:
                row["status"] = status
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
                rows.append({"schema": APPROVAL_SCHEMA, "status": "invalid_json", "raw": line})
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
