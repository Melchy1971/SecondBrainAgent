from __future__ import annotations

from dataclasses import dataclass, field

from .audit_log import ToolAuditEntry, ToolAuditLog
from .parameter_validator import ParameterValidator
from .permission_policy import ToolExecutionPolicy
from .tool_contract import ToolCall, ToolResult
from .tool_errors import ToolError, ToolExecutionError
from .tool_registry import ToolRegistry


@dataclass
class ToolExecutionAdapter:
    registry: ToolRegistry
    policy: ToolExecutionPolicy = field(default_factory=ToolExecutionPolicy)
    validator: ParameterValidator = field(default_factory=ParameterValidator)
    audit_log: ToolAuditLog = field(default_factory=ToolAuditLog)

    def execute(self, call: ToolCall) -> ToolResult:
        try:
            registered = self.registry.get(call.tool_name)
            definition = registered.definition
            self.policy.assert_allowed(definition)
            validated_args = self.validator.validate(definition, call.arguments)
            output = registered.handler(validated_args)
            result = ToolResult(tool_name=definition.name, success=True, output=output)
            self.audit_log.record(ToolAuditEntry(
                tool_name=definition.name,
                caller=call.caller,
                success=True,
                arguments=self.validator.sanitized(definition, validated_args),
                correlation_id=call.correlation_id,
            ))
            return result
        except ToolError as exc:
            self.audit_log.record(ToolAuditEntry(
                tool_name=call.tool_name,
                caller=call.caller,
                success=False,
                arguments=dict(call.arguments),
                error=str(exc),
                correlation_id=call.correlation_id,
            ))
            return ToolResult(tool_name=call.tool_name, success=False, error=str(exc))
        except Exception as exc:  # defensive boundary for arbitrary tool handlers
            wrapped = ToolExecutionError(str(exc))
            self.audit_log.record(ToolAuditEntry(
                tool_name=call.tool_name,
                caller=call.caller,
                success=False,
                arguments=dict(call.arguments),
                error=str(wrapped),
                correlation_id=call.correlation_id,
            ))
            return ToolResult(tool_name=call.tool_name, success=False, error=str(wrapped))
