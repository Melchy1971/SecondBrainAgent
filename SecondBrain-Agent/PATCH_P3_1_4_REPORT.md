# PATCH P3.1.4 — Agent Tool-Calling Framework

## Ziel
Tool-Aufrufe des Agenten erhalten einen stabilen Vertrag mit Registry, Parameterprüfung, Berechtigungs-/Approval-Regeln, Execution Adapter und Audit-Spur.

## Neue Dateien
- `secondbrain/agent/tools/tool_contract.py`
- `secondbrain/agent/tools/tool_errors.py`
- `secondbrain/agent/tools/tool_registry.py`
- `secondbrain/agent/tools/parameter_validator.py`
- `secondbrain/agent/tools/permission_policy.py`
- `secondbrain/agent/tools/audit_log.py`
- `secondbrain/agent/tools/execution_adapter.py`
- `tests/agent/tools/test_tool_calling_framework.py`

## Validierung
- Registry
- Validierung unbekannter/fehlender/falscher Parameter
- Permission-Gate
- Approval-Gate
- Handler-Ausführung
- Exception-Boundary
- Audit-Log mit Secret-Masking
