
from __future__ import annotations

from pathlib import Path
from typing import Any
import argparse
import json

from .launcher_runtime_v115 import SecondBrainLauncherV115
from .launcher_runtime_v113 import _print_json
from .api_bridge_v116 import ApiBridge, ApiServer


class SecondBrainLauncherV116(SecondBrainLauncherV115):
    def __init__(self, project_root: str | Path | None = None, profile: str | None = None):
        super().__init__(project_root, profile)
        self.api_bridge = ApiBridge(self.config.runtime_dir, self)
        self.workflow_host.register('api.status', lambda payload: self.api_status())
        self.workflow_host.register('api.dispatch', lambda payload: self.api_dispatch(payload.get('method','GET'), payload.get('path','/status'), payload.get('payload', {}), internal=True))


    # API-compatible aliases over existing launcher method names.
    def status(self) -> dict[str, Any]:
        return self.runtime_status()

    def capture(self, text: str, title: str = "API Capture") -> str:
        return str(self.quick_capture(text, title))

    def agent_run(self, objective: str, max_steps: int = 5) -> dict[str, Any]:
        return self.autonomous_run(objective, max_steps)

    def api_status(self) -> dict[str, Any]:
        return self.api_bridge.status()

    def api_manifest(self) -> dict[str, Any]:
        return self.api_bridge.manifest()

    def api_token_create(self, name: str, scopes: str = 'read:status') -> dict[str, Any]:
        scope_list = [s.strip() for s in scopes.split(',') if s.strip()]
        result = self.api_bridge.tokens.create(name, scope_list)
        self.emit('api.token_created', 'launcher_v116', {'token_id': result['token_id'], 'scopes': scope_list}, risk_level=2)
        return result

    def api_token_list(self) -> list[dict[str, Any]]:
        return self.api_bridge.tokens.list()

    def api_audit(self, limit: int = 20) -> list[dict[str, Any]]:
        return self.api_bridge.audit.tail(limit)

    def api_dispatch(self, method: str, path: str, payload: dict[str, Any] | None = None, token: str | None = None, internal: bool = False) -> dict[str, Any]:
        status, body = self.api_bridge.dispatch(method, path, payload or {}, token, internal)
        return {'http_status': status, **body}

    def api_serve(self, host: str = '127.0.0.1', port: int = 8765) -> None:
        ApiServer(self.api_bridge, host, port).serve_forever()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='secondbrain', description='SecondBrain OS v11.6 launcher')
    parser.add_argument('--project-root', default=str(Path.cwd()), help='SecondBrain-Agent Projektordner')
    parser.add_argument('--profile', default=None, help='Startprofil, z. B. safe/dev/local-ai')
    sub = parser.add_subparsers(dest='cmd', required=False)
    base_cmds = ['init','health','sync','tick','start','rag-index','agent-status','up','down','status','restart','diagnose','metrics','recover','workflow-status','twin-status','decision-history','voice-status','voice-session','voice-sessions','mobile-status','mobile-devices','mobile-push-list','mobile-captures','mobile-approvals','api-status','api-manifest','api-token-list','api-audit']
    for cmd in base_cmds:
        sub.add_parser(cmd)
    p_gui = sub.add_parser('gui'); p_gui.add_argument('--snapshot', action='store_true')
    p_api_tok = sub.add_parser('api-token-create'); p_api_tok.add_argument('name'); p_api_tok.add_argument('--scopes', default='read:status')
    p_api_call = sub.add_parser('api-dispatch'); p_api_call.add_argument('method'); p_api_call.add_argument('path'); p_api_call.add_argument('--payload', default='{}'); p_api_call.add_argument('--token', default=None); p_api_call.add_argument('--internal', action='store_true')
    p_api_srv = sub.add_parser('api-serve'); p_api_srv.add_argument('--host', default='127.0.0.1'); p_api_srv.add_argument('--port', type=int, default=8765)
    # Keep all v11.5 commands available by delegating unknown/base commands to legacy main.
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args, unknown = parser.parse_known_args(argv)
    cmd = args.cmd or 'status'
    launcher = SecondBrainLauncherV116(args.project_root, args.profile)
    try:
        if cmd == 'api-status': _print_json(launcher.api_status())
        elif cmd == 'api-manifest': _print_json(launcher.api_manifest())
        elif cmd == 'api-token-create': _print_json(launcher.api_token_create(args.name, args.scopes))
        elif cmd == 'api-token-list': _print_json(launcher.api_token_list())
        elif cmd == 'api-audit': _print_json(launcher.api_audit())
        elif cmd == 'api-dispatch': _print_json(launcher.api_dispatch(args.method, args.path, json.loads(args.payload), args.token, args.internal))
        elif cmd == 'api-serve': launcher.api_serve(args.host, args.port)
        else:
            from .launcher_runtime_v115 import main as legacy_main
            return legacy_main(argv)
        return 0
    except Exception as exc:
        print(f'ERROR: {exc}')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
