
from __future__ import annotations
from pathlib import Path
from typing import Any
import argparse, json

from .launcher_runtime_v124 import SecondBrainLauncherV124
from .launcher_runtime_v113 import _print_json
from .tool_registry_v121 import ToolDefinition
from .desktop_os import DesktopOSKernel

class SecondBrainLauncherV125(SecondBrainLauncherV124):
    def __init__(self, project_root: str | Path | None = None, profile: str | None = None):
        super().__init__(project_root, profile)
        self.desktop_v125 = DesktopOSKernel(
            self.config.runtime_dir,
            tool_registry=self.tool_registry_v121,
            service_status_provider=lambda: self.core124_status(),
        )
        self._register_desktop_tools()

    def _register_desktop_tools(self) -> None:
        defs = [
            ToolDefinition('desktop.status', 'Read desktop OS status', {'type': 'object', 'properties': {}}, {'type': 'object'}, ['desktop.read'], 1, False),
            ToolDefinition('desktop.dashboard', 'Read dashboard snapshot', {'type': 'object', 'properties': {}}, {'type': 'object'}, ['desktop.read'], 1, False),
            ToolDefinition('desktop.notify', 'Create desktop notification', {'type': 'object', 'required': ['title'], 'properties': {'title': {'type': 'string'}, 'body': {'type': 'string'}, 'level': {'type': 'string'}}}, {'type': 'object'}, ['desktop.write'], 1, False),
        ]
        handlers = {
            'desktop.status': lambda p: self.desktop_status(),
            'desktop.dashboard': lambda p: self.desktop_dashboard(),
            'desktop.notify': lambda p: self.desktop_notify(p.get('title',''), p.get('body',''), p.get('level','info')),
        }
        for definition in defs:
            self.tool_registry_v121.register(definition, handlers[definition.name])

    def desktop_status(self) -> dict[str, Any]:
        return self.desktop_v125.status()

    def desktop_open(self, view: str = 'dashboard') -> dict[str, Any]:
        return self.desktop_v125.open(view)

    def desktop_dashboard(self) -> dict[str, Any]:
        return self.desktop_v125.dashboard.snapshot()

    def desktop_activity(self) -> list[dict[str, Any]]:
        return self.desktop_v125.dashboard.activity_feed()

    def desktop_widgets(self) -> list[dict[str, Any]]:
        return self.desktop_v125.widgets.list()

    def desktop_widget_enable(self, widget_id: str, enabled: bool) -> list[dict[str, Any]]:
        return self.desktop_v125.widgets.set_enabled(widget_id, enabled)

    def desktop_commands(self, query: str | None = None) -> list[dict[str, Any]]:
        return self.desktop_v125.commands.list(query)

    def desktop_command(self, command_id: str, payload: str | None = None) -> dict[str, Any]:
        parsed = json.loads(payload) if payload else {}
        return self.desktop_v125.execute_command(command_id, parsed)

    def desktop_notify(self, title: str, body: str = '', level: str = 'info') -> dict[str, Any]:
        return self.desktop_v125.notifications.notify(title, body, level)

    def desktop_notifications(self, unread: bool = False, limit: int = 50) -> list[dict[str, Any]]:
        return self.desktop_v125.notifications.list(unread_only=unread, limit=limit)

    def desktop_session(self) -> dict[str, Any]:
        return self.desktop_v125.sessions.current()

    def core125_status(self) -> dict[str, Any]:
        base = self.core124_status()
        base.update({'version': '12.5', 'desktop': self.desktop_status()})
        return base

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='secondbrain', description='SecondBrain OS v12.5 launcher')
    parser.add_argument('--project-root', default=str(Path.cwd()))
    parser.add_argument('--profile', default=None)
    sub = parser.add_subparsers(dest='cmd', required=False)
    for cmd in ['core-status','desktop-status','desktop-dashboard','desktop-activity','desktop-widgets','desktop-commands','desktop-notifications','desktop-session']:
        sub.add_parser(cmd)
    p = sub.add_parser('desktop-open'); p.add_argument('--view', default='dashboard')
    p = sub.add_parser('desktop-widget-enable'); p.add_argument('widget_id'); p.add_argument('--enabled', choices=['true','false'], default='true')
    p = sub.add_parser('desktop-command'); p.add_argument('command_id'); p.add_argument('--payload', default=None)
    p = sub.add_parser('desktop-notify'); p.add_argument('title'); p.add_argument('--body', default=''); p.add_argument('--level', default='info')
    p = sub.add_parser('desktop-search-command'); p.add_argument('query')
    return parser

def main(argv: list[str] | None = None) -> int:
    import sys
    raw = list(sys.argv[1:] if argv is None else argv)
    v125_cmds = {'core-status','desktop-status','desktop-open','desktop-dashboard','desktop-activity','desktop-widgets','desktop-widget-enable','desktop-commands','desktop-search-command','desktop-command','desktop-notify','desktop-notifications','desktop-session'}
    first_cmd = next((x for x in raw if not x.startswith('-')), None)
    if first_cmd is not None and first_cmd not in v125_cmds:
        from .launcher_runtime_v124 import main as legacy_main
        return legacy_main(argv)
    parser = build_parser()
    args = parser.parse_args(argv)
    cmd = args.cmd or 'core-status'
    launcher = SecondBrainLauncherV125(args.project_root, args.profile)
    try:
        if cmd == 'core-status': _print_json(launcher.core125_status())
        elif cmd == 'desktop-status': _print_json(launcher.desktop_status())
        elif cmd == 'desktop-open': _print_json(launcher.desktop_open(args.view))
        elif cmd == 'desktop-dashboard': _print_json(launcher.desktop_dashboard())
        elif cmd == 'desktop-activity': _print_json(launcher.desktop_activity())
        elif cmd == 'desktop-widgets': _print_json(launcher.desktop_widgets())
        elif cmd == 'desktop-widget-enable': _print_json(launcher.desktop_widget_enable(args.widget_id, args.enabled == 'true'))
        elif cmd == 'desktop-commands': _print_json(launcher.desktop_commands())
        elif cmd == 'desktop-search-command': _print_json(launcher.desktop_commands(args.query))
        elif cmd == 'desktop-command': _print_json(launcher.desktop_command(args.command_id, args.payload))
        elif cmd == 'desktop-notify': _print_json(launcher.desktop_notify(args.title, args.body, args.level))
        elif cmd == 'desktop-notifications': _print_json(launcher.desktop_notifications())
        elif cmd == 'desktop-session': _print_json(launcher.desktop_session())
        else: return 2
        return 0
    except Exception as exc:
        print(f'ERROR: {exc}')
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
