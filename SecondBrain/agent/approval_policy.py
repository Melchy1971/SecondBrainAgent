from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Iterable, Mapping


@dataclass(frozen=True, slots=True)
class MandatoryApprovalDecision:
    action_type: str
    approval_category: str
    policy_rule: str
    policy_version: str
    effective_requires_approval: bool
    configured_requires_approval: bool

    def audit_fields(self) -> dict[str, Any]:
        return {
            "policy_rule": self.policy_rule,
            "policy_version": self.policy_version,
            "effective_requires_approval": self.effective_requires_approval,
            "configured_requires_approval": self.configured_requires_approval,
        }


class MandatoryApprovalPolicy:
    """Non-bypassable approval rules for destructive and external side effects."""

    VERSION = "mandatory-approval.v1"
    MANDATORY_ACTION_TYPES = frozenset(
        {
            "delete",
            "send",
            "forward",
            "publish",
            "external_write",
            "filesystem_write",
            "system_command",
            "permission_change",
            "credential_change",
            "connector_write",
        }
    )

    def evaluate_tool(self, tool: Any) -> MandatoryApprovalDecision:
        return self.evaluate(
            name=str(getattr(tool, "name", "")),
            category=str(getattr(tool, "category", "")),
            capabilities=getattr(tool, "capabilities", ()),
            scopes=getattr(tool, "scopes", ()),
            metadata=getattr(tool, "metadata", {}),
            risk_level=getattr(tool, "risk_level", "low"),
            configured_requires_approval=bool(getattr(tool, "requires_approval", False)),
        )

    def evaluate(
        self,
        *,
        name: str,
        category: str = "",
        capabilities: Iterable[Any] = (),
        scopes: Iterable[str] = (),
        metadata: Mapping[str, Any] | None = None,
        risk_level: Any = "low",
        configured_requires_approval: bool = False,
        action_type: str = "",
    ) -> MandatoryApprovalDecision:
        metadata = dict(metadata or {})
        explicit = self._normalize_action_type(action_type or str(metadata.get("action_type") or ""))
        detected = explicit if explicit in self.MANDATORY_ACTION_TYPES else self._detect_action_type(
            name=name,
            category=category,
            capabilities=capabilities,
            scopes=scopes,
            metadata=metadata,
        )
        risk = self._value(risk_level)
        if detected:
            rule = f"mandatory_action:{detected}"
        elif risk in {"high", "critical"}:
            detected = "unknown_high_risk"
            rule = f"default_deny:{risk}"
        elif configured_requires_approval:
            detected = "configured"
            rule = "configured_requires_approval"
        else:
            return MandatoryApprovalDecision(
                action_type="",
                approval_category="risky_agent_action",
                policy_rule="not_required",
                policy_version=self.VERSION,
                effective_requires_approval=False,
                configured_requires_approval=False,
            )

        return MandatoryApprovalDecision(
            action_type=detected,
            approval_category=self._approval_category(detected, category, metadata),
            policy_rule=rule,
            policy_version=self.VERSION,
            effective_requires_approval=True,
            configured_requires_approval=configured_requires_approval,
        )

    def _detect_action_type(
        self,
        *,
        name: str,
        category: str,
        capabilities: Iterable[Any],
        scopes: Iterable[str],
        metadata: Mapping[str, Any],
    ) -> str:
        capability_values = [self._value(item) for item in capabilities]
        if "system" in capability_values:
            return "system_command"
        metadata_values = [
            metadata.get("operation"),
            metadata.get("action"),
            metadata.get("side_effect"),
            metadata.get("action_category"),
        ]
        values = [name, category, *scopes, *capability_values, *metadata_values]
        tokens = set()
        normalized_values = []
        for value in values:
            normalized = self._normalize_action_type(str(value or ""))
            if normalized:
                normalized_values.append(normalized)
                tokens.update(normalized.split("_"))
                if normalized in self.MANDATORY_ACTION_TYPES:
                    return normalized
        joined = "_".join(normalized_values)

        if tokens & {"delete", "remove", "trash", "purge"}:
            return "delete"
        if "forward" in tokens:
            return "forward"
        if tokens & {"publish", "post"}:
            return "publish"
        if "send" in tokens or (tokens & {"email", "message"} and tokens & {"write", "create", "deliver"}):
            return "send"
        if "permission" in tokens or "permissions" in tokens or (
            tokens & {"scope", "role"} and tokens & {"change", "update", "write", "grant", "revoke"}
        ):
            return "permission_change"
        if tokens & {"credential", "credentials"} or (
            tokens & {"password", "secret", "token", "key"} and tokens & {"change", "update", "rotate", "write"}
        ):
            return "credential_change"
        write_tokens = {"write", "create", "update", "edit", "save", "upload", "move", "copy"}
        if "external" in tokens and tokens & write_tokens:
            return "external_write"
        if tokens & {"filesystem", "file"} and tokens & write_tokens:
            return "filesystem_write"
        if tokens & {"system", "shell", "command", "exec", "execute"} and tokens & {
            "command",
            "exec",
            "execute",
            "run",
            "shell",
        }:
            return "system_command"
        if "connector" in tokens and tokens & (write_tokens | {"sync", "push"}):
            return "connector_write"
        if "external_write" in joined:
            return "external_write"
        return ""

    @classmethod
    def _approval_category(cls, action_type: str, category: str, metadata: Mapping[str, Any]) -> str:
        sensitive = bool(metadata.get("sensitive_document")) or "sensitive_document" in cls._normalize_action_type(category)
        if sensitive:
            return "sensitive_document"
        if action_type == "delete":
            return "delete_request"
        if action_type == "permission_change":
            return "connector_permission_change"
        return "risky_agent_action"

    @staticmethod
    def _normalize_action_type(value: str) -> str:
        return re.sub(r"_+", "_", re.sub(r"[^a-z0-9]+", "_", value.strip().lower())).strip("_")

    @staticmethod
    def _value(value: Any) -> str:
        raw = getattr(value, "value", value)
        return str(raw or "").strip().lower()
