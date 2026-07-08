from __future__ import annotations

from pathlib import Path
from typing import Any
import argparse, json

from .launcher_runtime_v121 import SecondBrainLauncherV121
from .launcher_runtime_v113 import _print_json
from .real_connectors_v122 import RealConnectorRegistry
from .tool_registry_v121 import ToolDefinition


class SecondBrainLauncherV122(SecondBrainLauncherV121):
    def __init__(self, project_root: str | Path | None = None, profile: str | None = None):
        super().__init__(project_root, profile)
        self.real_connectors_v122 = RealConnectorRegistry(self.config.runtime_dir, self.event_bus_v121)
        self._register_connector_tools()

    def _register_connector_tools(self) -> None:
        defs = [
            ToolDefinition('connectors.status','Read connector status', {'type':'object','properties':{}}, {'type':'object'}, ['connectors.read'], 1, False),
            ToolDefinition('connectors.sync','Sync one connector', {'type':'object','required':['name'],'properties':{'name':{'type':'string'},'limit':{'type':'integer'}}}, {'type':'object'}, ['connectors.sync'], 2, False),
            ToolDefinition('connectors.sync_all','Sync all enabled connectors', {'type':'object','properties':{'limit':{'type':'integer'}}}, {'type':'object'}, ['connectors.sync'], 2, False),
        ]
        handlers = {
            'connectors.status': lambda p: self.connectors_status(),
            'connectors.sync': lambda p: self.connector_sync(p.get('name',''), int(p.get('limit',10))),
            'connectors.sync_all': lambda p: self.connector_sync_all(int(p.get('limit',10))),
        }
        for d in defs:
            self.tool_registry_v121.register(d, handlers[d.name])

    def connectors_status(self) -> dict[str, Any]:
        return self.real_connectors_v122.status()
    def connectors_list(self, enabled_only: bool = False) -> list[dict[str, Any]]:
        return self.real_connectors_v122.list_connectors(enabled_only)
    def connector_enable(self, name: str) -> dict[str, Any]:
        return self.real_connectors_v122.set_enabled(name, True)
    def connector_disable(self, name: str) -> dict[str, Any]:
        return self.real_connectors_v122.set_enabled(name, False)
    def connector_sync(self, name: str, limit: int = 10, force: bool = False) -> dict[str, Any]:
        return self.real_connectors_v122.sync(name, limit=limit, force=force).__dict__
    def connector_sync_all(self, limit: int = 10) -> list[dict[str, Any]]:
        return self.real_connectors_v122.sync_all(True, limit)
    def connector_runs(self, limit: int = 20) -> list[dict[str, Any]]:
        return self.real_connectors_v122.sync_runs(limit)
    def connector_queue(self) -> list[dict[str, Any]]:
        return self.real_connectors_v122.store.queue_items(100)
    def connector_queue_drain(self, max_items: int = 50) -> dict[str, Any]:
        return self.real_connectors_v122.drain_queue(max_items)
    def connector_webhook(self, name: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self.real_connectors_v122.receive_webhook(name, payload)
    def connector_webhooks(self, limit: int = 20) -> list[dict[str, Any]]:
        return self.real_connectors_v122.webhook_inbox(limit)
    def connector_oauth_templates(self) -> list[dict[str, Any]]:
        return self.real_connectors_v122.oauth_templates()
    def core122_status(self) -> dict[str, Any]:
        base=self.core121_status()
        base.update({'version':'12.2','real_connectors':self.connectors_status()})
        return base


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='secondbrain', description='SecondBrain OS v12.2 launcher')
    parser.add_argument('--project-root', default=str(Path.cwd()))
    parser.add_argument('--profile', default=None)
    sub=parser.add_subparsers(dest='cmd', required=False)
    for cmd in ['core-status','connectors-status','connectors-list','connector-runs','connector-queue','connector-queue-drain','connector-webhooks','connector-oauth-templates']:
        sub.add_parser(cmd)
    p=sub.add_parser('connector-enable'); p.add_argument('name')
    p=sub.add_parser('connector-disable'); p.add_argument('name')
    p=sub.add_parser('connector-sync'); p.add_argument('name'); p.add_argument('--limit', type=int, default=10); p.add_argument('--force', action='store_true')
    p=sub.add_parser('connector-sync-all'); p.add_argument('--limit', type=int, default=10)
    p=sub.add_parser('connector-webhook'); p.add_argument('name'); p.add_argument('payload', nargs='?', default='{}')
    return parser


def main(argv: list[str] | None = None) -> int:
    import sys
    raw=list(sys.argv[1:] if argv is None else argv)
    v122_cmds={'core-status','connectors-status','connectors-list','connector-enable','connector-disable','connector-sync','connector-sync-all','connector-runs','connector-queue','connector-queue-drain','connector-webhook','connector-webhooks','connector-oauth-templates'}
    first_cmd=next((x for x in raw if not x.startswith('-')), None)
    if first_cmd is not None and first_cmd not in v122_cmds:
        from .launcher_runtime_v121 import main as legacy_main
        return legacy_main(argv)
    parser=build_parser(); args=parser.parse_args(argv); cmd=args.cmd or 'core-status'
    launcher=SecondBrainLauncherV122(args.project_root, args.profile)
    try:
        if cmd=='core-status': _print_json(launcher.core122_status())
        elif cmd=='connectors-status': _print_json(launcher.connectors_status())
        elif cmd=='connectors-list': _print_json(launcher.connectors_list())
        elif cmd=='connector-enable': _print_json(launcher.connector_enable(args.name))
        elif cmd=='connector-disable': _print_json(launcher.connector_disable(args.name))
        elif cmd=='connector-sync': _print_json(launcher.connector_sync(args.name, args.limit, args.force))
        elif cmd=='connector-sync-all': _print_json(launcher.connector_sync_all(args.limit))
        elif cmd=='connector-runs': _print_json(launcher.connector_runs())
        elif cmd=='connector-queue': _print_json(launcher.connector_queue())
        elif cmd=='connector-queue-drain': _print_json(launcher.connector_queue_drain())
        elif cmd=='connector-webhook': _print_json(launcher.connector_webhook(args.name, json.loads(args.payload)))
        elif cmd=='connector-webhooks': _print_json(launcher.connector_webhooks())
        elif cmd=='connector-oauth-templates': _print_json(launcher.connector_oauth_templates())
        else: return 2
        return 0
    except Exception as exc:
        print(f'ERROR: {exc}')
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
