from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Callable
import json
import time

ToolHandler = Callable[[dict[str, Any]], Any]

@dataclass
class ToolDefinition:
    name: str
    description: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    scopes: list[str]
    risk_level: int = 1
    requires_approval: bool = False
    enabled: bool = True

class ToolRegistry:
    def __init__(self, runtime_dir: str | Path):
        self.root = Path(runtime_dir) / 'tools_v121'
        self.root.mkdir(parents=True, exist_ok=True)
        self.manifest_file = self.root / 'tool_manifest.json'
        self.audit_file = self.root / 'tool_audit.jsonl'
        self._handlers: dict[str, ToolHandler] = {}
        self._tools: dict[str, ToolDefinition] = {}
        self._load_manifest()

    def _load_manifest(self) -> None:
        if not self.manifest_file.exists():
            return
        for row in json.loads(self.manifest_file.read_text(encoding='utf-8')):
            self._tools[row['name']] = ToolDefinition(**row)

    def _save_manifest(self) -> None:
        rows = [asdict(v) for v in sorted(self._tools.values(), key=lambda x: x.name)]
        self.manifest_file.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding='utf-8')

    def register(self, definition: ToolDefinition, handler: ToolHandler | None = None) -> dict[str, Any]:
        self._tools[definition.name] = definition
        if handler is not None:
            self._handlers[definition.name] = handler
        self._save_manifest()
        return asdict(definition)

    def list(self, scope: str | None = None, enabled: bool | None = None) -> list[dict[str, Any]]:
        rows = [asdict(t) for t in self._tools.values()]
        if scope:
            rows = [r for r in rows if scope in r.get('scopes', [])]
        if enabled is not None:
            rows = [r for r in rows if bool(r.get('enabled')) is enabled]
        return sorted(rows, key=lambda r: r['name'])

    def get(self, name: str) -> dict[str, Any]:
        if name not in self._tools:
            raise KeyError(f'Unknown tool: {name}')
        return asdict(self._tools[name])

    def set_enabled(self, name: str, enabled: bool) -> dict[str, Any]:
        if name not in self._tools:
            raise KeyError(f'Unknown tool: {name}')
        self._tools[name].enabled = enabled
        self._save_manifest()
        return asdict(self._tools[name])

    def _validate(self, definition: ToolDefinition, payload: dict[str, Any], scopes: list[str], approved: bool) -> None:
        missing_scope = [s for s in definition.scopes if s not in scopes]
        if missing_scope:
            raise PermissionError(f'Missing scopes: {missing_scope}')
        if not definition.enabled:
            raise PermissionError(f'Tool disabled: {definition.name}')
        if definition.requires_approval and not approved:
            raise PermissionError(f'Approval required for tool: {definition.name}')
        required = definition.input_schema.get('required', []) if isinstance(definition.input_schema, dict) else []
        missing = [k for k in required if k not in payload]
        if missing:
            raise ValueError(f'Missing required fields: {missing}')

    def execute(self, name: str, payload: dict[str, Any] | None = None, scopes: list[str] | None = None, approved: bool = False) -> dict[str, Any]:
        if name not in self._tools:
            raise KeyError(f'Unknown tool: {name}')
        definition = self._tools[name]
        payload = payload or {}
        scopes = scopes or []
        self._validate(definition, payload, scopes, approved)
        started = time.time()
        try:
            result = self._handlers[name](payload) if name in self._handlers else {'status': 'accepted', 'payload': payload}
            status = 'success'
            return {'tool': name, 'status': status, 'risk_level': definition.risk_level, 'result': result}
        except Exception as exc:
            status = 'failed'
            raise
        finally:
            row = {'tool': name, 'status': status, 'payload': payload, 'duration_ms': int((time.time()-started)*1000), 'created_at': time.time()}
            with self.audit_file.open('a', encoding='utf-8') as f:
                f.write(json.dumps(row, ensure_ascii=False, sort_keys=True)+'\n')

    def audit(self, limit: int = 50) -> list[dict[str, Any]]:
        if not self.audit_file.exists():
            return []
        rows = [json.loads(x) for x in self.audit_file.read_text(encoding='utf-8').splitlines() if x.strip()]
        return rows[-limit:]

    def status(self) -> dict[str, Any]:
        rows = self.list()
        return {'component': 'tool_registry_v121', 'tools': len(rows), 'enabled': sum(1 for r in rows if r['enabled']), 'healthy': True}
