from __future__ import annotations

from dataclasses import dataclass, field

from .tool_contract import ToolDefinition, ToolPermission, ToolRisk
from .tool_errors import ToolApprovalRequired, ToolPermissionError


@dataclass
class ToolExecutionPolicy:
    allowed_permissions: set[ToolPermission] = field(default_factory=lambda: {ToolPermission.READ})
    auto_approve_low_risk: bool = True
    approved_tools: set[str] = field(default_factory=set)

    def assert_allowed(self, definition: ToolDefinition) -> None:
        missing = set(definition.permissions) - self.allowed_permissions
        if missing:
            names = ", ".join(sorted(permission.value for permission in missing))
            raise ToolPermissionError(f"missing permission(s): {names}")

        approval_needed = definition.requires_approval or definition.risk in {ToolRisk.MEDIUM, ToolRisk.HIGH}
        if approval_needed and definition.name not in self.approved_tools:
            if definition.risk == ToolRisk.LOW and self.auto_approve_low_risk:
                return
            raise ToolApprovalRequired(f"approval required for tool: {definition.name}")
