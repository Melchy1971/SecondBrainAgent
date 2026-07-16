"""Single tool contract and registry used by AgentCore and the runtime."""

from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping
from uuid import uuid4

from .approval_policy import MandatoryApprovalDecision, MandatoryApprovalPolicy


ToolHandler = Callable[[Mapping[str, Any]], Any]
RollbackHandler = Callable[[Mapping[str, Any], Any], Any]


DEFAULT_TOOL_CATEGORIES: tuple[str, ...] = (
    "search",
    "document",
    "connector",
    "calendar",
    "email",
    "file",
    "workflow",
    "memory",
    "system",
)

_CATEGORY_ALIASES: dict[str, str] = {
    "documents": "document",
    "doc": "document",
    "import": "connector",
    "imports": "connector",
    "github": "connector",
    "filesystem": "file",
    "files": "file",
    "jobs": "workflow",
    "agents": "workflow",
    "notifications": "system",
    "settings": "system",
    "voice": "system",
    "updates": "system",
}


class ToolRegistryError(ValueError):
    pass


class ToolRiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @property
    def severity(self) -> int:
        return {self.LOW: 1, self.MEDIUM: 2, self.HIGH: 3, self.CRITICAL: 4}[self]

    @classmethod
    def parse(cls, value: Any) -> "ToolRiskLevel":
        if isinstance(value, cls):
            return value
        if isinstance(value, int):
            return {1: cls.LOW, 2: cls.MEDIUM, 3: cls.HIGH, 4: cls.CRITICAL}.get(value, cls.CRITICAL)
        normalized = str(value or "low").strip().lower()
        aliases = {"read": cls.LOW, "write": cls.HIGH, "execute": cls.HIGH, "system": cls.CRITICAL}
        try:
            return aliases.get(normalized) or cls(normalized)
        except ValueError as exc:
            raise ToolRegistryError(f"invalid_tool_risk:{value}") from exc


class ToolCapability(StrEnum):
    SEARCH = "search"
    DOCUMENT = "document"
    CONNECTOR = "connector"
    CALENDAR = "calendar"
    EMAIL = "email"
    FILE = "file"
    WORKFLOW_CORE = "workflow"
    MEMORY_CORE = "memory"
    SYSTEM_CORE = "system"
    DOCUMENTS = "documents"
    IMPORT = "import"
    MEMORY = "memory"
    AGENTS = "agents"
    JOBS = "jobs"
    NOTIFICATIONS = "notifications"
    SETTINGS = "settings"
    VOICE = "voice"
    UPDATES = "updates"
    GITHUB = "github"
    FILESYSTEM = "filesystem"
    SYSTEM = "system"
    RAG = "rag"
    WORKFLOW = "workflow"
    DELETE = "delete"
    SEND = "send"
    FORWARD = "forward"
    PUBLISH = "publish"
    EXTERNAL_WRITE = "external_write"
    FILESYSTEM_WRITE = "filesystem_write"
    SYSTEM_COMMAND = "system_command"
    PERMISSION_CHANGE = "permission_change"
    CREDENTIAL_CHANGE = "credential_change"
    CONNECTOR_WRITE = "connector_write"

    @classmethod
    def parse(cls, value: Any) -> "ToolCapability":
        if isinstance(value, cls):
            return value
        normalized = str(value or "").strip().lower()
        aliases = {
            "documents": cls.DOCUMENT,
            "document": cls.DOCUMENT,
            "import": cls.CONNECTOR,
            "filesystem": cls.FILE,
            "file": cls.FILE,
            "workflow": cls.WORKFLOW,
            "memory": cls.MEMORY,
            "system": cls.SYSTEM,
        }
        try:
            return aliases.get(normalized) or cls(normalized)
        except ValueError as exc:
            raise ToolRegistryError(f"invalid_tool_capability:{value}") from exc


_JSON_TYPES: dict[str, type | tuple[type, ...]] = {
    "string": str,
    "integer": int,
    "number": (int, float),
    "boolean": bool,
    "array": list,
    "object": dict,
    "null": type(None),
}


@dataclass(frozen=True, slots=True)
class ToolInputSchema:
    properties: dict[str, dict[str, Any]] = field(default_factory=dict)
    required: tuple[str, ...] = ()
    additional_properties: bool = True

    @classmethod
    def from_value(cls, value: "ToolInputSchema | Mapping[str, Any] | None") -> "ToolInputSchema":
        if isinstance(value, cls):
            return value
        schema = dict(value or {})
        return cls(
            properties={str(key): dict(item) for key, item in dict(schema.get("properties") or {}).items()},
            required=tuple(str(item) for item in schema.get("required") or ()),
            additional_properties=bool(schema.get("additionalProperties", True)),
        )

    def validate(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        values = dict(payload)
        missing = [name for name in self.required if name not in values]
        if missing:
            raise ToolRegistryError(f"missing_required_input:{','.join(missing)}")
        unknown = set(values) - set(self.properties)
        if unknown and not self.additional_properties:
            raise ToolRegistryError(f"unknown_tool_input:{','.join(sorted(unknown))}")
        for name, value in values.items():
            spec = self.properties.get(name)
            if not spec or value is None:
                continue
            expected_name = str(spec.get("type") or "")
            expected = _JSON_TYPES.get(expected_name)
            if expected and (expected_name == "integer" and isinstance(value, bool) or not isinstance(value, expected)):
                raise ToolRegistryError(f"invalid_tool_input_type:{name}:{expected_name}")
        return values

    def sanitize(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        return {
            key: "***" if bool(self.properties.get(key, {}).get("sensitive")) else value
            for key, value in payload.items()
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": self.properties,
            "required": list(self.required),
            "additionalProperties": self.additional_properties,
        }


@dataclass(frozen=True, slots=True)
class ToolResult:
    tool_name: str
    success: bool
    output: Any = None
    error: str | None = None
    duration_ms: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.success

    @property
    def status(self) -> str:
        return "success" if self.success else "failed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool": self.tool_name,
            "tool_name": self.tool_name,
            "ok": self.success,
            "success": self.success,
            "status": self.status,
            "result": self.output,
            "output": self.output,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "metadata": dict(self.metadata),
        }


@dataclass(init=False)
class ToolDefinition:
    name: str
    description: str
    category: str
    input_schema: ToolInputSchema
    output_schema: dict[str, Any]
    risk_level: ToolRiskLevel
    requires_approval: bool
    enabled: bool
    handler: ToolHandler | None
    rollback_handler: RollbackHandler | None
    capabilities: tuple[ToolCapability, ...]
    scopes: tuple[str, ...]
    parameters: tuple[Any, ...]
    permissions: tuple[Any, ...]
    timeout_seconds: float
    retry_count: int
    metadata: dict[str, Any]

    def __init__(
        self,
        name: str,
        description: str,
        *legacy: Any,
        category: str = "general",
        input_schema: ToolInputSchema | Mapping[str, Any] | None = None,
        output_schema: Mapping[str, Any] | None = None,
        risk_level: ToolRiskLevel | str | int = ToolRiskLevel.LOW,
        requires_approval: bool = False,
        enabled: bool = True,
        handler: ToolHandler | None = None,
        capabilities: Iterable[ToolCapability | str] = (),
        scopes: Iterable[str] = (),
        parameters: Iterable[Any] = (),
        permissions: Iterable[Any] = (),
        risk: ToolRiskLevel | str | int | None = None,
        timeout_seconds: float = 30.0,
        retry_count: int = 0,
        rollback_handler: RollbackHandler | None = None,
        metadata: Mapping[str, Any] | None = None,
        requires_confirmation: bool | None = None,
    ) -> None:
        # v21: ToolDefinition(name, description, handler)
        # v121: ToolDefinition(name, description, input, output, scopes, risk, approval, enabled)
        if legacy and callable(legacy[0]):
            handler = legacy[0]
        elif legacy and isinstance(legacy[0], str):
            # Unified positional contract follows the documented field order.
            category = legacy[0]
            if len(legacy) > 1:
                input_schema = legacy[1]
            if len(legacy) > 2:
                output_schema = legacy[2]
            if len(legacy) > 3:
                risk_level = legacy[3]
            if len(legacy) > 4:
                requires_approval = bool(legacy[4])
            if len(legacy) > 5:
                enabled = bool(legacy[5])
            if len(legacy) > 6:
                handler = legacy[6]
            if len(legacy) > 7:
                raise TypeError("too many positional ToolDefinition arguments")
        elif legacy:
            input_schema = legacy[0]
            if len(legacy) > 1:
                output_schema = legacy[1]
            if len(legacy) > 2:
                scopes = legacy[2]
            if len(legacy) > 3:
                risk_level = legacy[3]
            if len(legacy) > 4:
                requires_approval = bool(legacy[4])
            if len(legacy) > 5:
                enabled = bool(legacy[5])
            if len(legacy) > 6:
                raise TypeError("too many positional ToolDefinition arguments")
        parameter_tuple = tuple(parameters)
        if parameter_tuple and input_schema is None:
            properties = {
                item.name: {
                    "type": _parameter_json_type(item.type_name),
                    "description": item.description,
                    "sensitive": bool(item.sensitive),
                }
                for item in parameter_tuple
            }
            input_schema = {
                "type": "object",
                "properties": properties,
                "required": [item.name for item in parameter_tuple if item.required and item.default is None],
                "additionalProperties": False,
            }
        self.name = str(name).strip()
        self.description = str(description).strip()
        self.category = _normalize_category(category)
        self.input_schema = ToolInputSchema.from_value(input_schema)
        self.output_schema = dict(output_schema or {})
        self.risk_level = ToolRiskLevel.parse(risk if risk is not None else risk_level)
        explicit_approval = bool(requires_approval if requires_confirmation is None else requires_confirmation)
        self.requires_approval = explicit_approval or self.risk_level in {ToolRiskLevel.HIGH, ToolRiskLevel.CRITICAL}
        self.enabled = bool(enabled)
        self.handler = handler
        self.rollback_handler = rollback_handler
        self.capabilities = tuple(ToolCapability.parse(item) for item in capabilities)
        self.scopes = tuple(str(item) for item in scopes)
        self.parameters = parameter_tuple
        self.permissions = tuple(permissions)
        self.timeout_seconds = max(0.001, float(timeout_seconds))
        self.retry_count = max(0, int(retry_count))
        self.metadata = dict(metadata or {})
        self.validate()

    @property
    def requires_confirmation(self) -> bool:
        return self.requires_approval

    @property
    def risk(self) -> ToolRiskLevel:
        return self.risk_level

    @property
    def definition(self) -> "ToolDefinition":
        return self

    def validate(self) -> None:
        if not self.name:
            raise ToolRegistryError("tool_name_required")
        if not self.description:
            raise ToolRegistryError("tool_description_required")
        if self.handler is not None and not callable(self.handler):
            raise ToolRegistryError("tool_handler_not_callable")
        if self.rollback_handler is not None and not callable(self.rollback_handler):
            raise ToolRegistryError("tool_rollback_handler_not_callable")
        unknown_required = set(self.input_schema.required) - set(self.input_schema.properties) if self.input_schema.properties else set()
        if unknown_required:
            raise ToolRegistryError(f"required_input_schema_missing:{','.join(sorted(unknown_required))}")

    def parameter_map(self) -> dict[str, Any]:
        return {parameter.name: parameter for parameter in self.parameters}

    def with_runtime(self, *, handler: ToolHandler | None = None, enabled: bool | None = None) -> "ToolDefinition":
        return ToolDefinition.from_dict(
            self.to_dict(include_handler=False),
            handler=self.handler if handler is None else handler,
            enabled=self.enabled if enabled is None else enabled,
            parameters=self.parameters,
            permissions=self.permissions,
            rollback_handler=self.rollback_handler,
        )

    def to_dict(self, *, include_handler: bool = False) -> dict[str, Any]:
        payload = {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "input_schema": self.input_schema.to_dict(),
            "output_schema": dict(self.output_schema),
            "risk_level": self.risk_level.value,
            "risk_severity": self.risk_level.severity,
            "requires_approval": self.requires_approval,
            "enabled": self.enabled,
            "capabilities": [item.value for item in self.capabilities],
            "scopes": list(self.scopes),
            "timeout_seconds": self.timeout_seconds,
            "retry_count": self.retry_count,
            "metadata": dict(self.metadata),
        }
        if include_handler:
            payload["handler"] = self.handler
        return payload

    @classmethod
    def from_dict(
        cls,
        payload: Mapping[str, Any],
        *,
        handler: ToolHandler | None = None,
        rollback_handler: RollbackHandler | None = None,
        enabled: bool | None = None,
        parameters: Iterable[Any] = (),
        permissions: Iterable[Any] = (),
    ) -> "ToolDefinition":
        data = dict(payload)
        return cls(
            str(data["name"]),
            str(data.get("description") or data["name"]),
            category=str(data.get("category") or "general"),
            input_schema=data.get("input_schema"),
            output_schema=data.get("output_schema"),
            risk_level=data.get("risk_level", 1),
            requires_approval=bool(data.get("requires_approval", False)),
            enabled=bool(data.get("enabled", True) if enabled is None else enabled),
            handler=handler,
            capabilities=data.get("capabilities") or (),
            scopes=data.get("scopes") or (),
            parameters=parameters,
            permissions=permissions,
            timeout_seconds=float(data.get("timeout_seconds", 30.0)),
            retry_count=int(data.get("retry_count", 0)),
            rollback_handler=rollback_handler,
            metadata=data.get("metadata") or {},
        )

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        if self.handler is None:
            raise ToolRegistryError(f"tool_handler_missing:{self.name}")
        return self.handler(*args, **kwargs)

    def __getitem__(self, key: str) -> Any:
        return self.to_dict()[key]


@dataclass(frozen=True, slots=True)
class ToolHealth:
    name: str
    healthy: bool
    enabled: bool
    handler_available: bool
    issues: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "healthy": self.healthy,
            "enabled": self.enabled,
            "handler_available": self.handler_available,
            "issues": list(self.issues),
        }


class ToolRegistry:
    """Canonical registry with optional persistence in the existing v121 store."""

    def __init__(self, runtime_dir: str | Path | None = None) -> None:
        self._tools: dict[str, ToolDefinition] = {}
        self._lock = threading.RLock()
        self.approval_policy = MandatoryApprovalPolicy()
        self._approval_lookup: Callable[[str], Mapping[str, Any] | None] | None = None
        self.root = Path(runtime_dir).resolve() / "tools_v121" if runtime_dir is not None else None
        self.manifest_file = self.root / "tool_manifest.json" if self.root else None
        self.audit_file = self.root / "tool_audit.jsonl" if self.root else None
        if self.root:
            self.root.mkdir(parents=True, exist_ok=True)
            self._load_manifest()

    def register(
        self,
        tool: ToolDefinition | str,
        handler: ToolHandler | None = None,
        *,
        replace: bool = False,
    ) -> ToolDefinition:
        if isinstance(tool, str):
            if handler is None:
                raise ToolRegistryError("tool_handler_not_callable")
            tool = ToolDefinition(tool, tool, handler)
        elif handler is not None:
            tool = tool.with_runtime(handler=handler)
        tool.validate()
        with self._lock:
            existing = self._tools.get(tool.name)
            if existing and not replace and existing.handler is not None:
                raise ToolRegistryError(f"tool_already_registered:{tool.name}")
            if existing:
                tool = tool.with_runtime(
                    handler=tool.handler or existing.handler,
                    enabled=existing.enabled,
                )
            self._tools[tool.name] = tool
            self._save_manifest()
        return tool

    def upsert(self, tool: ToolDefinition, handler: ToolHandler | None = None) -> ToolDefinition:
        return self.register(tool, handler, replace=True)

    def unregister(self, name: str) -> None:
        with self._lock:
            self._tools.pop(name, None)
            self._save_manifest()

    def get(self, name: str) -> ToolDefinition:
        try:
            return self._tools[name]
        except KeyError as exc:
            raise ToolRegistryError(f"tool_not_found:{name}") from exc

    def has(self, name: str) -> bool:
        return name in self._tools

    contains = has

    def list(
        self,
        scope: str | None = None,
        enabled: bool | None = None,
        *,
        enabled_only: bool | None = None,
        category: str | None = None,
    ) -> list[ToolDefinition]:
        tools = list(self._tools.values())
        effective_enabled = enabled if enabled is not None else (True if enabled_only is True else None)
        if effective_enabled is not None:
            tools = [tool for tool in tools if tool.enabled is effective_enabled]
        if scope:
            tools = [tool for tool in tools if scope in tool.scopes]
        if category:
            tools = [tool for tool in tools if tool.category == category]
        return sorted(tools, key=lambda tool: (tool.category, tool.name))

    def list_definitions(self) -> list[ToolDefinition]:
        return self.list()

    def set_enabled(self, name: str, enabled: bool) -> ToolDefinition:
        with self._lock:
            current = self.get(name)
            updated = current.with_runtime(enabled=enabled)
            self._tools[name] = updated
            self._save_manifest()
        return updated

    def set_approval_lookup(self, lookup: Callable[[str], Mapping[str, Any] | None]) -> None:
        self._approval_lookup = lookup

    def run(
        self,
        name: str,
        payload: Mapping[str, Any] | None = None,
        *,
        scopes: Iterable[str] | None = None,
        approved: bool = False,
        approval: Mapping[str, Any] | None = None,
    ) -> ToolResult:
        started = time.perf_counter()
        values = dict(payload or {})
        tool: ToolDefinition | None = None
        policy: MandatoryApprovalDecision | None = None
        _ = approved  # Retained for API compatibility; a Boolean is not approval evidence.
        try:
            tool = self.get(name)
            policy = self.approval_policy.evaluate_tool(tool)
            if not tool.enabled:
                raise ToolRegistryError(f"tool_disabled:{name}")
            if policy.effective_requires_approval and not self._approval_matches(tool, values, approval):
                raise ToolRegistryError(f"tool_requires_approval:{name}:{policy.policy_rule}")
            if scopes is not None:
                missing = set(tool.scopes) - set(scopes)
                if missing:
                    raise ToolRegistryError(f"missing_tool_scopes:{','.join(sorted(missing))}")
            validated = tool.input_schema.validate(values)
            safe_payload = tool.input_schema.sanitize(validated)
            if tool.handler is None:
                raise ToolRegistryError(f"tool_handler_missing:{name}")
            attempts = 0
            output = None
            last_error: Exception | None = None
            for attempts in range(1, tool.retry_count + 2):
                try:
                    output = _invoke_with_timeout(tool.handler, validated, tool.timeout_seconds)
                    last_error = None
                    break
                except Exception as exc:  # noqa: BLE001 - attempt errors are normalized in result
                    last_error = exc
                    if attempts >= tool.retry_count + 1:
                        raise
            if last_error is not None:
                raise last_error
            _validate_output(tool.output_schema, output)
            result = ToolResult(
                name,
                True,
                output=output,
                duration_ms=_elapsed_ms(started),
                metadata={
                    "risk_level": tool.risk_level.value,
                    "attempts": attempts,
                    **policy.audit_fields(),
                },
            )
        except Exception as exc:
            metadata = {"risk_level": tool.risk_level.value if tool else "unknown"}
            if "attempts" in locals():
                metadata["attempts"] = attempts
            if policy is not None:
                metadata.update(policy.audit_fields())
            result = ToolResult(name, False, error=str(exc), duration_ms=_elapsed_ms(started), metadata=metadata)
        self._audit(tool, result, values, policy)
        return result

    def rollback(self, name: str, payload: Mapping[str, Any] | None = None, result: Any = None) -> dict[str, Any]:
        tool = self.get(name)
        if tool.rollback_handler is None:
            return {"ok": True, "status": "no_rollback", "tool": name}
        values = dict(payload or {})
        started = time.perf_counter()
        try:
            outcome = _invoke_with_timeout(lambda current: tool.rollback_handler(current, result), values, tool.timeout_seconds)
            row = {
                "tool": name,
                "status": "rollback_success",
                "payload": tool.input_schema.sanitize(values),
                "error": None,
                "duration_ms": _elapsed_ms(started),
                "created_at": time.time(),
                "event": "rollback",
            }
            if self.audit_file:
                with self.audit_file.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            return {"ok": True, "status": "rollback_success", "tool": name, "result": outcome}
        except Exception as exc:  # noqa: BLE001 - rollback failures must be isolated
            row = {
                "tool": name,
                "status": "rollback_failed",
                "payload": tool.input_schema.sanitize(values),
                "error": str(exc),
                "duration_ms": _elapsed_ms(started),
                "created_at": time.time(),
                "event": "rollback",
            }
            if self.audit_file:
                with self.audit_file.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            return {"ok": False, "status": "rollback_failed", "tool": name, "error": str(exc)}

    def execute(
        self,
        name: str,
        payload: Mapping[str, Any] | None = None,
        scopes: Iterable[str] | None = None,
        approved: bool = False,
        *,
        confirmed: bool = False,
        approval: Mapping[str, Any] | None = None,
    ) -> Any:
        legacy_runtime = scopes is not None
        _ = approved, confirmed  # Compatibility-only flags; never authorization evidence.
        result = self.run(name, payload, scopes=scopes, approval=approval)
        if not result.success:
            error = result.error or f"tool_execution_failed:{name}"
            if not legacy_runtime and "tool_requires_approval" in error:
                raise ToolRegistryError(error.replace("tool_requires_approval", "tool_requires_confirmation"))
            if "scope" in error or "approval" in error or "disabled" in error:
                raise PermissionError(error)
            raise ToolRegistryError(error)
        if legacy_runtime:
            risk = self.get(name).risk_level
            return {
                "tool": name,
                "status": "success",
                "risk_level": risk.severity,
                "result": result.output,
                "duration_ms": result.duration_ms,
            }
        return result.output

    def health(self, name: str | None = None) -> dict[str, Any]:
        tools = [self.get(name)] if name else self.list(enabled_only=False)
        rows: list[ToolHealth] = []
        for tool in tools:
            issues = []
            if not tool.enabled:
                issues.append("disabled")
            if tool.handler is None:
                issues.append("handler_missing")
            rows.append(ToolHealth(tool.name, not issues, tool.enabled, tool.handler is not None, tuple(issues)))
        return {
            "component": "unified_tool_registry",
            "healthy": all(row.healthy for row in rows),
            "tools": len(rows),
            "enabled": sum(row.enabled for row in rows),
            "handlers": sum(row.handler_available for row in rows),
            "checks": [row.to_dict() for row in rows],
        }

    status = health

    def audit(self, limit: int = 50) -> list[dict[str, Any]]:
        if not self.audit_file or not self.audit_file.exists():
            return []
        rows = []
        for line in self.audit_file.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return rows[-max(0, int(limit)):]

    def _audit(
        self,
        tool: ToolDefinition | None,
        result: ToolResult,
        payload: Mapping[str, Any],
        policy: MandatoryApprovalDecision | None = None,
    ) -> None:
        if not self.audit_file:
            return
        row = {
            "tool": result.tool_name,
            "status": result.status,
            "payload": dict(payload),
            "error": result.error,
            "duration_ms": result.duration_ms,
            "created_at": time.time(),
            "event": "tool_run",
            "metadata": dict(result.metadata),
        }
        if policy is not None:
            row.update(policy.audit_fields())
        with self.audit_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    def _approval_matches(
        self,
        tool: ToolDefinition,
        payload: Mapping[str, Any],
        approval: Mapping[str, Any] | None,
    ) -> bool:
        if not isinstance(approval, Mapping) or not approval.get("approval_id"):
            return False
        if self._approval_lookup is None:
            return False
        persisted = self._approval_lookup(str(approval["approval_id"]))
        if not isinstance(persisted, Mapping) or persisted.get("status") != "approved":
            return False
        approved_tool = str(persisted.get("tool_name") or persisted.get("command") or "")
        if approved_tool != tool.name:
            return False
        approved_payload = persisted.get("payload")
        if not isinstance(approved_payload, Mapping):
            return False
        return dict(approved_payload) == tool.input_schema.sanitize(payload)

    def _load_manifest(self) -> None:
        if not self.manifest_file or not self.manifest_file.exists():
            return
        raw = self.manifest_file.read_text(encoding="utf-8").strip()
        if not raw:
            return
        try:
            rows = json.loads(raw)
        except json.JSONDecodeError:
            return
        if not isinstance(rows, list):
            return
        for row in rows:
            if isinstance(row, dict) and row.get("name"):
                try:
                    definition = ToolDefinition.from_dict(row)
                    self._tools[definition.name] = definition
                except (KeyError, TypeError, ValueError):
                    continue

    def _save_manifest(self) -> None:
        if not self.manifest_file:
            return
        rows = [tool.to_dict() for tool in sorted(self._tools.values(), key=lambda item: item.name)]
        temporary = self.manifest_file.with_name(f"{self.manifest_file.name}.{uuid4().hex}.tmp")
        temporary.write_text(json.dumps(rows, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        for attempt in range(3):
            try:
                temporary.replace(self.manifest_file)
                break
            except PermissionError:
                if attempt == 2:
                    temporary.unlink(missing_ok=True)
                    raise
                time.sleep(0.01 * (attempt + 1))


def _parameter_json_type(type_name: str) -> str:
    return {"str": "string", "int": "integer", "float": "number", "bool": "boolean", "list": "array", "dict": "object"}.get(type_name, type_name)


def _elapsed_ms(started: float) -> int:
    return int((time.perf_counter() - started) * 1000)


def _normalize_category(category: str | None) -> str:
    return str(category or "general").strip().lower() or "general"


def _invoke_with_timeout(handler: Callable[..., Any], payload: Mapping[str, Any], timeout_seconds: float, **kwargs: Any) -> Any:
    box: dict[str, Any] = {}

    def _runner() -> None:
        try:
            box["result"] = handler(payload, **kwargs)
        except Exception as exc:  # noqa: BLE001 - normalized by caller
            box["error"] = exc

    thread = threading.Thread(target=_runner, daemon=True)
    thread.start()
    thread.join(max(0.001, float(timeout_seconds)))
    if thread.is_alive():
        raise TimeoutError(f"tool_timeout:{timeout_seconds}")
    if "error" in box:
        raise box["error"]
    return box.get("result")


def _validate_output(schema: Mapping[str, Any], output: Any) -> None:
    expected_name = str(schema.get("type") or "")
    expected = _JSON_TYPES.get(expected_name)
    if expected and output is not None and not isinstance(output, expected):
        raise ToolRegistryError(f"invalid_tool_output_type:{expected_name}")
