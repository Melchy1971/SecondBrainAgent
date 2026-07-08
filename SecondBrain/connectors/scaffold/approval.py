"""Approval gate for writing Graph actions.

Every mutating Graph call goes through ApprovalGate.guard(). Default policy is
DENY: a pending ApprovalRequest is recorded and ApprovalRequired is raised. A
write only executes after explicit approve(request_id) (or auto_approve=True for
non-interactive/automated contexts the operator opted into).
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from hashlib import sha256
from pathlib import Path
from threading import RLock
from typing import Any, Callable, Protocol


class ApprovalRequired(RuntimeError):
    def __init__(self, request: "ApprovalRequest") -> None:
        super().__init__(f"approval required for {request.action} ({request.request_id})")
        self.request = request


@dataclass(frozen=True)
class ApprovalRequest:
    request_id: str
    action: str          # e.g. "mail.send"
    resource: str        # e.g. "mail"
    method: str          # HTTP method
    target: str          # endpoint / recipient summary
    summary: str
    created_at: float
    status: str = "pending"   # pending | approved | denied

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ApprovalStore(Protocol):
    def put(self, request: ApprovalRequest) -> None: ...
    def get(self, request_id: str) -> ApprovalRequest | None: ...
    def set_status(self, request_id: str, status: str) -> ApprovalRequest | None: ...
    def list(self) -> list[ApprovalRequest]: ...


class InMemoryApprovalStore:
    def __init__(self) -> None:
        self._items: dict[str, ApprovalRequest] = {}
        self._lock = RLock()

    def put(self, request: ApprovalRequest) -> None:
        with self._lock:
            self._items.setdefault(request.request_id, request)

    def get(self, request_id: str) -> ApprovalRequest | None:
        with self._lock:
            return self._items.get(request_id)

    def set_status(self, request_id: str, status: str) -> ApprovalRequest | None:
        with self._lock:
            cur = self._items.get(request_id)
            if cur is None:
                return None
            updated = ApprovalRequest(**{**cur.to_dict(), "status": status})
            self._items[request_id] = updated
            return updated

    def list(self) -> list[ApprovalRequest]:
        with self._lock:
            return list(self._items.values())


class JsonApprovalStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._lock = RLock()

    def _read(self) -> dict[str, dict]:
        if not self.path.exists():
            return {}
        text = self.path.read_text(encoding="utf-8").strip()
        return json.loads(text) if text else {}

    def _write(self, data: dict[str, dict]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
        tmp.replace(self.path)

    def put(self, request: ApprovalRequest) -> None:
        with self._lock:
            data = self._read()
            data.setdefault(request.request_id, request.to_dict())
            self._write(data)

    def get(self, request_id: str) -> ApprovalRequest | None:
        raw = self._read().get(request_id)
        return ApprovalRequest(**raw) if raw else None

    def set_status(self, request_id: str, status: str) -> ApprovalRequest | None:
        with self._lock:
            data = self._read()
            if request_id not in data:
                return None
            data[request_id]["status"] = status
            self._write(data)
            return ApprovalRequest(**data[request_id])

    def list(self) -> list[ApprovalRequest]:
        return [ApprovalRequest(**raw) for raw in self._read().values()]


class ApprovalGate:
    def __init__(
        self,
        store: ApprovalStore | None = None,
        *,
        auto_approve: bool = False,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.store = store or InMemoryApprovalStore()
        self.auto_approve = auto_approve
        self.clock = clock

    @staticmethod
    def request_id(action: str, target: str, payload: Any) -> str:
        blob = json.dumps({"a": action, "t": target, "p": payload}, sort_keys=True, default=str)
        return sha256(blob.encode("utf-8")).hexdigest()[:16]

    def guard(
        self,
        action: str,
        resource: str,
        method: str,
        target: str,
        payload: Any,
        execute: Callable[[], Any],
    ) -> Any:
        rid = self.request_id(action, target, payload)
        existing = self.store.get(rid)
        approved = self.auto_approve or (existing is not None and existing.status == "approved")
        if approved:
            return execute()
        if existing is None:
            self.store.put(ApprovalRequest(
                request_id=rid, action=action, resource=resource, method=method,
                target=target, summary=_summarize(payload), created_at=self.clock(),
            ))
        elif existing.status == "denied":
            raise ApprovalRequired(existing)
        raise ApprovalRequired(self.store.get(rid))

    def approve(self, request_id: str) -> ApprovalRequest | None:
        return self.store.set_status(request_id, "approved")

    def deny(self, request_id: str) -> ApprovalRequest | None:
        return self.store.set_status(request_id, "denied")

    def pending(self) -> list[ApprovalRequest]:
        return [r for r in self.store.list() if r.status == "pending"]


def _summarize(payload: Any) -> str:
    text = json.dumps(payload, default=str) if not isinstance(payload, str) else payload
    return text[:200]
