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
from typing import Any, Callable, Mapping, Protocol

from secondbrain.agent.approval_service import AgentApprovalService


class ApprovalRequired(RuntimeError):
    def __init__(self, request: "ApprovalRequest") -> None:
        super().__init__(f"approval required for {request.action} ({request.request_id})")
        self.request = request


class ApprovalBindingMismatch(PermissionError):
    pass


class ApprovalExpired(PermissionError):
    pass


class ApprovalConflict(PermissionError):
    pass


@dataclass(frozen=True)
class ConnectorActionDecision:
    connector_id: str
    action: str
    effective_scopes: tuple[str, ...]
    requested_scopes: tuple[str, ...]
    added_scopes: tuple[str, ...]
    removed_scopes: tuple[str, ...]
    risk_level: str
    requires_approval: bool
    approval_category: str = "connector_permission_change"
    policy_rule: str = "read_only"

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        for field_name in ("effective_scopes", "requested_scopes", "added_scopes", "removed_scopes"):
            value[field_name] = list(value[field_name])
        return value


class ConnectorActionPolicy:
    """Central default-deny policy for connector permissions and writes."""

    WRITE_TOKENS = frozenset({
        "send", "forward", "publish", "create", "update", "modify", "delete",
        "remove", "upload", "write", "post", "draft", "credential", "scope",
        "permission", "workspace", "issue", "pull_request", "disable",
    })
    READ_TOKENS = frozenset({"status", "health", "search", "sync", "read", "list", "fetch", "get"})

    def evaluate(
        self,
        *,
        connector_id: str,
        action: str,
        method: str = "GET",
        effective_scopes: tuple[str, ...] | list[str] = (),
        requested_scopes: tuple[str, ...] | list[str] | None = None,
        payload: Mapping[str, Any] | None = None,
    ) -> ConnectorActionDecision:
        effective = self._scopes(effective_scopes)
        requested = self._scopes(requested_scopes if requested_scopes is not None else effective)
        added = tuple(scope for scope in requested if scope not in effective)
        removed = tuple(scope for scope in effective if scope not in requested)
        normalized = action.strip().lower().replace("-", "_")
        tokens = {token for part in normalized.replace(".", "_").split("_") for token in (part,) if token}
        mutating_method = method.strip().upper() not in {"GET", "HEAD", "OPTIONS"}
        payload_data = dict(payload or {})
        data_loss_disable = "disable" in tokens and bool(payload_data.get("data_loss_risk", True))
        write_action = bool(tokens & self.WRITE_TOKENS) or mutating_method or data_loss_disable
        requires_approval = bool(added) or write_action
        if "credential" in tokens:
            risk, rule = "critical", "credential_change"
        elif added:
            risk, rule = "high", "scope_expansion"
        elif write_action:
            risk, rule = "high", "connector_write"
        elif tokens & self.READ_TOKENS:
            risk, rule = "low", "read_only"
        else:
            risk, rule = "low", "read_only_unknown"
        return ConnectorActionDecision(
            connector_id=connector_id,
            action=action,
            effective_scopes=effective,
            requested_scopes=requested,
            added_scopes=added,
            removed_scopes=removed,
            risk_level=risk,
            requires_approval=requires_approval,
            policy_rule=rule,
        )

    @staticmethod
    def _scopes(scopes: tuple[str, ...] | list[str]) -> tuple[str, ...]:
        return tuple(sorted({str(scope).strip() for scope in scopes if str(scope).strip()}))


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
    approval_id: str = ""
    connector_id: str = ""
    workspace_id: str = "default"
    actor: str = "connector_user"
    effective_scopes: tuple[str, ...] = ()
    requested_scopes: tuple[str, ...] = ()
    added_scopes: tuple[str, ...] = ()
    removed_scopes: tuple[str, ...] = ()
    risk_level: str = "high"
    requires_approval: bool = True
    approval_category: str = "connector_permission_change"
    payload_hash: str = ""
    binding_hash: str = ""
    expires_at: float = 0.0

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
        project_root: str | Path | None = None,
        connector_id: str = "",
        workspace_id: str = "default",
        actor: str = "connector_user",
        effective_scopes: tuple[str, ...] | list[str] = (),
        approval_ttl_seconds: float = 900.0,
        approval_service: AgentApprovalService | None = None,
        policy: ConnectorActionPolicy | None = None,
    ) -> None:
        self.store = store or InMemoryApprovalStore()
        self.auto_approve = auto_approve
        self.clock = clock
        self.connector_id = connector_id
        self.workspace_id = workspace_id or "default"
        self.actor = actor or "connector_user"
        self.effective_scopes = tuple(effective_scopes)
        self.approval_ttl_seconds = max(1.0, float(approval_ttl_seconds))
        self.policy = policy or ConnectorActionPolicy()
        inferred_root = project_root or (self._root_for_json_store(store) if isinstance(store, JsonApprovalStore) else None)
        self.approval_service = approval_service or (AgentApprovalService(inferred_root) if inferred_root is not None else None)

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
        *,
        approval_id: str = "",
        connector_id: str = "",
        workspace_id: str = "",
        actor: str = "",
        effective_scopes: tuple[str, ...] | list[str] | None = None,
        requested_scopes: tuple[str, ...] | list[str] | None = None,
    ) -> Any:
        resolved_connector = connector_id or self.connector_id or resource
        resolved_workspace = workspace_id or self.workspace_id
        resolved_actor = actor or self.actor
        current_scopes = tuple(self.effective_scopes if effective_scopes is None else effective_scopes)
        decision = self.policy.evaluate(
            connector_id=resolved_connector,
            action=action,
            method=method,
            effective_scopes=current_scopes,
            requested_scopes=requested_scopes,
            payload=payload if isinstance(payload, Mapping) else None,
        )
        if not decision.requires_approval:
            return execute()
        if self.approval_service is None:
            return self._legacy_guard(action, resource, method, target, payload, execute, decision)

        payload_hash = self._hash(payload)
        binding = {
            "connector_id": resolved_connector,
            "workspace_id": resolved_workspace,
            "actor": resolved_actor,
            "action": action,
            "method": method.upper(),
            "target": target,
            "effective_scopes": list(decision.effective_scopes),
            "requested_scopes": list(decision.requested_scopes),
            "added_scopes": list(decision.added_scopes),
            "removed_scopes": list(decision.removed_scopes),
            "payload_hash": payload_hash,
            "policy_rule": decision.policy_rule,
        }
        binding_hash = self._hash(binding)
        binding["binding_hash"] = binding_hash
        approval = self._bound_approval(binding_hash, approval_id)
        if approval is None:
            expires_at = self.clock() + self.approval_ttl_seconds
            approval = self.approval_service.create_connector_approval(
                connector_id=resolved_connector,
                workspace_id=resolved_workspace,
                action=action,
                actor=resolved_actor,
                binding=binding,
                risk_level=decision.risk_level,
                expires_at=expires_at,
            )
        stored_binding = approval.get("payload") if isinstance(approval.get("payload"), dict) else {}
        if stored_binding.get("binding_hash") != binding_hash:
            raise ApprovalBindingMismatch("connector_approval_binding_mismatch")
        expires_at = float(stored_binding.get("expires_at") or 0.0)
        status = str(approval.get("status") or "pending")
        request = self._native_request(approval)
        if status == "executed":
            raise ApprovalConflict("connector_approval_already_consumed")
        if status != "approved":
            raise ApprovalRequired(request)
        if not expires_at or self.clock() >= expires_at:
            raise ApprovalExpired("connector_approval_expired")
        result = execute()
        self.approval_service.queue.transition(
            str(approval["approval_id"]),
            "executed",
            actor="connector_executor",
            note="Bound connector action executed exactly once.",
        )
        return result

    def _legacy_guard(
        self,
        action: str,
        resource: str,
        method: str,
        target: str,
        payload: Any,
        execute: Callable[[], Any],
        decision: ConnectorActionDecision,
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
                connector_id=decision.connector_id,
                effective_scopes=decision.effective_scopes,
                requested_scopes=decision.requested_scopes,
                added_scopes=decision.added_scopes,
                removed_scopes=decision.removed_scopes,
                risk_level=decision.risk_level,
                requires_approval=decision.requires_approval,
                payload_hash=self._hash(payload),
            ))
        elif existing.status == "denied":
            raise ApprovalRequired(existing)
        raise ApprovalRequired(self.store.get(rid))

    def approve(self, request_id: str, actor: str = "connector_reviewer") -> ApprovalRequest | None:
        if self.approval_service is not None:
            approval = self.approval_service.get(request_id)
            if approval is None:
                return None
            payload = approval.get("payload") if isinstance(approval.get("payload"), dict) else {}
            if self.clock() >= float(payload.get("expires_at") or 0.0):
                raise ApprovalExpired("connector_approval_expired")
            return self._native_request(self.approval_service.approve(request_id, actor))
        return self.store.set_status(request_id, "approved")

    def deny(self, request_id: str, actor: str = "connector_reviewer") -> ApprovalRequest | None:
        if self.approval_service is not None:
            approval = self.approval_service.get(request_id)
            if approval is None:
                return None
            return self._native_request(self.approval_service.reject(request_id, actor))
        return self.store.set_status(request_id, "denied")

    def pending(self) -> list[ApprovalRequest]:
        if self.approval_service is not None:
            return [
                self._native_request(row)
                for row in self.approval_service.list_pending()
                if row.get("category") == "connector_permission_change"
            ]
        return [r for r in self.store.list() if r.status == "pending"]

    def _bound_approval(self, binding_hash: str, approval_id: str) -> dict[str, Any] | None:
        if self.approval_service is None:
            return None
        if approval_id:
            approval = self.approval_service.get(approval_id)
            if approval is None:
                raise KeyError(f"connector_approval_not_found:{approval_id}")
            return approval
        for approval in reversed(self.approval_service.queue.list()):
            payload = approval.get("payload") if isinstance(approval.get("payload"), dict) else {}
            if payload.get("binding_hash") == binding_hash:
                return approval
        return None

    @staticmethod
    def _native_request(approval: Mapping[str, Any]) -> ApprovalRequest:
        payload = approval.get("payload") if isinstance(approval.get("payload"), dict) else {}
        status = "denied" if approval.get("status") == "rejected" else str(approval.get("status") or "pending")
        approval_id = str(approval.get("approval_id") or "")
        return ApprovalRequest(
            request_id=approval_id,
            approval_id=approval_id,
            action=str(payload.get("action") or approval.get("intent") or ""),
            resource=str(payload.get("connector_id") or approval.get("target") or ""),
            method=str(payload.get("method") or "POST"),
            target=str(payload.get("target") or approval.get("target") or ""),
            summary="Bound connector permission request",
            created_at=_timestamp(approval.get("created_at")),
            status=status,
            connector_id=str(payload.get("connector_id") or ""),
            workspace_id=str(payload.get("workspace_id") or approval.get("workspace_id") or "default"),
            actor=str(payload.get("actor") or "connector_user"),
            effective_scopes=tuple(payload.get("effective_scopes") or ()),
            requested_scopes=tuple(payload.get("requested_scopes") or ()),
            added_scopes=tuple(payload.get("added_scopes") or ()),
            removed_scopes=tuple(payload.get("removed_scopes") or ()),
            risk_level=str(approval.get("risk_level") or "high"),
            payload_hash=str(payload.get("payload_hash") or ""),
            binding_hash=str(payload.get("binding_hash") or ""),
            expires_at=float(payload.get("expires_at") or 0.0),
        )

    @staticmethod
    def _hash(value: Any) -> str:
        blob = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
        return sha256(blob.encode("utf-8")).hexdigest()

    @staticmethod
    def _root_for_json_store(store: JsonApprovalStore | None) -> Path | None:
        if store is None:
            return None
        parent = store.path.resolve().parent
        if parent.name == "connectors" and parent.parent.name == "runtime":
            return parent.parent.parent
        return parent


def _summarize(payload: Any) -> str:
    if isinstance(payload, Mapping):
        return json.dumps({"fields": sorted(str(key) for key in payload), "items": len(payload)})[:200]
    return type(payload).__name__


def _timestamp(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    try:
        from datetime import datetime
        return datetime.fromisoformat(str(value)).timestamp()
    except (TypeError, ValueError):
        return 0.0
