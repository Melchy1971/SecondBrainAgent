from __future__ import annotations

from typing import Any, Mapping

from .tool_contract import ToolDefinition
from .tool_errors import ToolValidationError

_TYPE_MAP = {
    "str": str,
    "int": int,
    "float": (float, int),
    "bool": bool,
    "list": list,
    "dict": dict,
}


class ParameterValidator:
    def validate(self, definition: ToolDefinition, arguments: Mapping[str, Any]) -> dict[str, Any]:
        params = definition.parameter_map()
        unknown = set(arguments) - set(params)
        if unknown:
            raise ToolValidationError(f"unknown parameter(s): {', '.join(sorted(unknown))}")

        validated: dict[str, Any] = {}
        for name, param in params.items():
            if name not in arguments:
                if param.required and param.default is None:
                    raise ToolValidationError(f"missing required parameter: {name}")
                validated[name] = param.default
                continue

            value = arguments[name]
            expected = _TYPE_MAP.get(param.type_name)
            if expected is None:
                raise ToolValidationError(f"unsupported parameter type: {param.type_name}")
            if value is None and not param.required:
                validated[name] = None
                continue
            if not isinstance(value, expected):
                raise ToolValidationError(f"parameter {name} must be {param.type_name}")
            validated[name] = value
        return validated

    def sanitized(self, definition: ToolDefinition, arguments: Mapping[str, Any]) -> dict[str, Any]:
        params = definition.parameter_map()
        return {key: "***" if params.get(key) and params[key].sensitive else value for key, value in arguments.items()}
