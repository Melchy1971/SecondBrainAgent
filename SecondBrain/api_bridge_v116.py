
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable
import argparse
import hashlib
import hmac
import json
import secrets
import threading
import urllib.parse


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return default


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
    tmp.replace(path)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


@dataclass
class ApiToken:
    token_id: str
    name: str
    token_hash: str
    scopes: list[str]
    created_at: str
    last_used_at: str | None = None
    enabled: bool = True


class ApiTokenStore:
    def __init__(self, runtime_dir: str | Path):
        self.base = Path(runtime_dir) / 'api_bridge'
        self.path = self.base / 'tokens.json'
        self.base.mkdir(parents=True, exist_ok=True)

    def create(self, name: str, scopes: list[str] | None = None) -> dict[str, Any]:
        scopes = scopes or ['read:status']
        token = 'sb_' + secrets.token_urlsafe(32)
        rec = ApiToken(
            token_id=secrets.token_hex(8),
            name=name,
            token_hash=_hash_token(token),
            scopes=scopes,
            created_at=_utc(),
        )
        rows = _read_json(self.path, [])
        rows.append(asdict(rec))
        _write_json(self.path, rows)
        out = asdict(rec)
        out['token'] = token
        out.pop('token_hash', None)
        return out

    def list(self) -> list[dict[str, Any]]:
        rows = _read_json(self.path, [])
        for row in rows:
            row.pop('token_hash', None)
        return rows

    def authenticate(self, token: str, required_scope: str) -> dict[str, Any]:
        rows = _read_json(self.path, [])
        token_hash = _hash_token(token)
        for row in rows:
            if row.get('enabled') and hmac.compare_digest(row.get('token_hash',''), token_hash):
                scopes = row.get('scopes', [])
                if required_scope not in scopes and '*' not in scopes:
                    raise PermissionError(f'missing scope: {required_scope}')
                row['last_used_at'] = _utc()
                _write_json(self.path, rows)
                clean = dict(row); clean.pop('token_hash', None)
                return clean
        raise PermissionError('invalid api token')


@dataclass
class ApiRoute:
    method: str
    path: str
    scope: str
    risk: int
    handler: Callable[[dict[str, Any]], Any]
    description: str


class ApiAuditLog:
    def __init__(self, runtime_dir: str | Path):
        self.path = Path(runtime_dir) / 'api_bridge' / 'audit.jsonl'
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, event: dict[str, Any]) -> None:
        event = {'ts': _utc(), **event}
        with self.path.open('a', encoding='utf-8') as f:
            f.write(json.dumps(event, ensure_ascii=False) + '\n')

    def tail(self, limit: int = 20) -> list[dict[str, Any]]:
        if not self.path.exists(): return []
        lines = self.path.read_text(encoding='utf-8').splitlines()[-limit:]
        return [json.loads(x) for x in lines if x.strip()]


class ApiBridge:
    def __init__(self, runtime_dir: str | Path, launcher: Any):
        self.runtime_dir = Path(runtime_dir)
        self.launcher = launcher
        self.tokens = ApiTokenStore(self.runtime_dir)
        self.audit = ApiAuditLog(self.runtime_dir)
        self.routes: dict[tuple[str,str], ApiRoute] = {}
        self._register_default_routes()

    def register(self, method: str, path: str, scope: str, risk: int, handler: Callable[[dict[str, Any]], Any], description: str) -> None:
        self.routes[(method.upper(), path)] = ApiRoute(method.upper(), path, scope, risk, handler, description)

    def _register_default_routes(self) -> None:
        self.register('GET', '/health', 'read:status', 1, lambda p: self.launcher.health(), 'Runtime healthcheck')
        self.register('GET', '/status', 'read:status', 1, lambda p: self.launcher.status(), 'Runtime status')
        self.register('GET', '/metrics', 'read:metrics', 1, lambda p: self.launcher.metrics(), 'Runtime metrics')
        self.register('GET', '/mobile/status', 'read:mobile', 1, lambda p: self.launcher.mobile_status(), 'Mobile bridge status')
        self.register('GET', '/voice/status', 'read:voice', 1, lambda p: self.launcher.voice_status(), 'Voice runtime status')
        self.register('GET', '/twin/status', 'read:twin', 1, lambda p: self.launcher.twin_status(), 'Digital twin status')
        self.register('POST', '/capture', 'write:capture', 2, lambda p: self.launcher.capture(p.get('text',''), p.get('title','API Capture')), 'Create quick capture')
        self.register('POST', '/notify', 'write:notify', 2, lambda p: self.launcher.notify(p.get('message',''), p.get('severity','info')), 'Create notification')
        self.register('POST', '/agent/run', 'execute:agent', 3, lambda p: self.launcher.agent_run(p.get('objective',''), int(p.get('max_steps', 5))), 'Run autonomous agent')
        self.register('POST', '/workflow/run', 'execute:workflow', 3, lambda p: self.launcher.workflow_run(p.get('name','api_workflow'), p.get('objective','')), 'Run workflow')

    def manifest(self) -> dict[str, Any]:
        return {
            'version': '11.6',
            'routes': [
                {'method': r.method, 'path': r.path, 'scope': r.scope, 'risk': r.risk, 'description': r.description}
                for r in self.routes.values()
            ]
        }

    def dispatch(self, method: str, path: str, payload: dict[str, Any] | None, token: str | None = None, internal: bool = False) -> tuple[int, dict[str, Any]]:
        method = method.upper(); payload = payload or {}
        if path == '/manifest' and method == 'GET':
            return 200, self.manifest()
        route = self.routes.get((method, path))
        if not route:
            return 404, {'ok': False, 'error': 'route_not_found', 'method': method, 'path': path}
        actor = {'token_id': 'internal'}
        try:
            if not internal:
                if not token: raise PermissionError('missing bearer token')
                actor = self.tokens.authenticate(token, route.scope)
            # Risk gate: level >=3 must either be internal or explicitly confirmed in payload.
            if route.risk >= 3 and not internal and not payload.get('approved'):
                raise PermissionError('approval required for risk >= 3')
            result = route.handler(payload)
            self.audit.write({'ok': True, 'method': method, 'path': path, 'risk': route.risk, 'actor': actor.get('token_id')})
            return 200, {'ok': True, 'result': result}
        except Exception as exc:
            self.audit.write({'ok': False, 'method': method, 'path': path, 'risk': route.risk, 'actor': actor.get('token_id'), 'error': str(exc)})
            code = 403 if isinstance(exc, PermissionError) else 500
            return code, {'ok': False, 'error': str(exc)}

    def status(self) -> dict[str, Any]:
        return {'version': '11.6', 'routes': len(self.routes), 'tokens': len(self.tokens.list()), 'audit_events': len(self.audit.tail(1000))}


def make_handler(bridge: ApiBridge):
    class Handler(BaseHTTPRequestHandler):
        server_version = 'SecondBrainAPI/11.6'
        def _send(self, status: int, body: dict[str, Any]):
            raw = json.dumps(body, ensure_ascii=False, indent=2).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type','application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(raw)))
            self.end_headers(); self.wfile.write(raw)
        def _token(self) -> str | None:
            auth = self.headers.get('Authorization','')
            if auth.lower().startswith('bearer '): return auth.split(' ',1)[1].strip()
            return None
        def _payload(self) -> dict[str, Any]:
            n = int(self.headers.get('Content-Length','0') or '0')
            if n <= 0: return {}
            raw = self.rfile.read(n).decode('utf-8')
            return json.loads(raw) if raw.strip() else {}
        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            status, body = bridge.dispatch('GET', parsed.path, {}, self._token())
            self._send(status, body)
        def do_POST(self):
            parsed = urllib.parse.urlparse(self.path)
            status, body = bridge.dispatch('POST', parsed.path, self._payload(), self._token())
            self._send(status, body)
        def log_message(self, fmt, *args):
            return
    return Handler


class ApiServer:
    def __init__(self, bridge: ApiBridge, host: str = '127.0.0.1', port: int = 8765):
        self.bridge = bridge; self.host = host; self.port = port; self.httpd: ThreadingHTTPServer | None = None
    def serve_forever(self) -> None:
        self.httpd = ThreadingHTTPServer((self.host, self.port), make_handler(self.bridge))
        print(f'SecondBrain API v11.6 listening on http://{self.host}:{self.port}')
        self.httpd.serve_forever()
