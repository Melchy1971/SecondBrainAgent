from __future__ import annotations

from pathlib import Path
from typing import Any
import argparse
import json

from .launcher_runtime_v120 import SecondBrainLauncherV120
from .launcher_runtime_v113 import _print_json
from .event_bus_v121 import EventBus
from .tool_registry_v121 import ToolDefinition, ToolRegistry
from .long_running_runtime_v121 import LongRunningRuntime

class SecondBrainLauncherV121(SecondBrainLauncherV120):
    def __init__(self, project_root: str | Path | None = None, profile: str | None = None):
        super().__init__(project_root, profile)
        self.event_bus_v121 = EventBus(self.config.runtime_dir)
        self.tool_registry_v121 = ToolRegistry(self.config.runtime_dir)
        self._register_core_tools()
        self.long_runtime_v121 = LongRunningRuntime(self.config.runtime_dir, self.event_bus_v121, self.tool_registry_v121)

    def _register_core_tools(self) -> None:
        defs = [
            ToolDefinition('system.status','Read local system status', {'type':'object','properties':{}}, {'type':'object'}, ['system.read'], 1, False),
            ToolDefinition('rag.answer','Answer with local RAG context', {'type':'object','required':['query'],'properties':{'query':{'type':'string'}}}, {'type':'object'}, ['rag.read'], 2, False),
            ToolDefinition('agent.run','Run autonomous agent objective', {'type':'object','required':['objective'],'properties':{'objective':{'type':'string'}}}, {'type':'object'}, ['agent.execute'], 3, True),
            ToolDefinition('workflow.run','Run workflow objective', {'type':'object','required':['name','objective'],'properties':{'name':{'type':'string'},'objective':{'type':'string'}}}, {'type':'object'}, ['workflow.execute'], 3, True),
        ]
        handlers = {
            'system.status': lambda p: self.status(),
            'rag.answer': lambda p: self.rag_answer(p.get('query','')),
            'agent.run': lambda p: self.agent_run(p.get('objective','')),
            'workflow.run': lambda p: self.workflow_run(p.get('name','Tool Workflow'), p.get('objective','')),
        }
        for d in defs:
            self.tool_registry_v121.register(d, handlers.get(d.name))

    # Event Bus
    def bus_status(self) -> dict[str, Any]:
        return self.event_bus_v121.status()
    def bus_publish(self, topic: str, payload: dict[str, Any] | None = None, source: str = 'launcher_v121', risk: int = 1) -> dict[str, Any]:
        return self.event_bus_v121.publish(topic, source, payload or {}, risk)
    def bus_events(self, topic: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
        return self.event_bus_v121.replay(topic, limit)
    def bus_dlq(self, limit: int = 20) -> list[dict[str, Any]]:
        return self.event_bus_v121.dead_letters(limit)
    def bus_subscribe(self, pattern: str, subscriber: str, persistent: bool = True) -> dict[str, Any]:
        return self.event_bus_v121.subscribe(pattern, subscriber, None, persistent)

    # Tools
    def tool_status(self) -> dict[str, Any]:
        return self.tool_registry_v121.status()
    def tool_list(self, scope: str | None = None) -> list[dict[str, Any]]:
        return self.tool_registry_v121.list(scope)
    def tool_execute(self, name: str, payload: dict[str, Any], scopes: list[str], approved: bool = False) -> dict[str, Any]:
        return self.long_runtime_v121.run_tool(name, payload, scopes, approved)
    def tool_audit(self, limit: int = 20) -> list[dict[str, Any]]:
        return self.tool_registry_v121.audit(limit)

    # Long Runtime
    def runtime121_status(self) -> dict[str, Any]:
        return self.long_runtime_v121.status()
    def runtime121_start(self) -> dict[str, Any]:
        return self.long_runtime_v121.start()
    def runtime121_stop(self) -> dict[str, Any]:
        return self.long_runtime_v121.stop()
    def runtime121_tick(self) -> dict[str, Any]:
        return self.long_runtime_v121.tick()
    def runtime121_recover(self) -> dict[str, Any]:
        return self.long_runtime_v121.recover()
    def runtime121_runs(self, limit: int = 20) -> list[dict[str, Any]]:
        return self.long_runtime_v121.runs(limit)

    def core121_status(self) -> dict[str, Any]:
        return {
            'version': '12.1',
            'event_bus': self.bus_status(),
            'tool_registry': self.tool_status(),
            'long_runtime': self.runtime121_status(),
        }

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='secondbrain', description='SecondBrain OS v12.1 launcher')
    parser.add_argument('--project-root', default=str(Path.cwd()))
    parser.add_argument('--profile', default=None)
    sub = parser.add_subparsers(dest='cmd', required=False)
    for cmd in ['core-status','bus-status','bus-dlq','tool-status','tool-list','tool-audit','runtime-status','runtime-start','runtime-stop','runtime-tick','runtime-recover','runtime-runs']:
        sub.add_parser(cmd)
    p_pub=sub.add_parser('bus-publish'); p_pub.add_argument('topic'); p_pub.add_argument('payload', nargs='?', default='{}'); p_pub.add_argument('--risk', type=int, default=1)
    p_ev=sub.add_parser('bus-events'); p_ev.add_argument('--topic', default=None); p_ev.add_argument('--limit', type=int, default=20)
    p_sub=sub.add_parser('bus-subscribe'); p_sub.add_argument('pattern'); p_sub.add_argument('subscriber')
    p_tl=sub.add_parser('tools'); p_tl.add_argument('--scope', default=None)
    p_tx=sub.add_parser('tool-execute'); p_tx.add_argument('name'); p_tx.add_argument('payload', nargs='?', default='{}'); p_tx.add_argument('--scopes', default=''); p_tx.add_argument('--approved', action='store_true')
    return parser

def main(argv: list[str] | None = None) -> int:
    import sys
    raw=list(sys.argv[1:] if argv is None else argv)
    v121_cmds={'core-status','bus-status','bus-dlq','bus-publish','bus-events','bus-subscribe','tool-status','tool-list','tools','tool-execute','tool-audit','runtime-status','runtime-start','runtime-stop','runtime-tick','runtime-recover','runtime-runs'}
    first_cmd=next((x for x in raw if not x.startswith('-')), None)
    if first_cmd is not None and first_cmd not in v121_cmds:
        from .launcher_runtime_v120 import main as legacy_main
        return legacy_main(argv)
    parser=build_parser(); args=parser.parse_args(argv); cmd=args.cmd or 'core-status'
    launcher=SecondBrainLauncherV121(args.project_root, args.profile)
    try:
        if cmd=='core-status': _print_json(launcher.core121_status())
        elif cmd=='bus-status': _print_json(launcher.bus_status())
        elif cmd=='bus-publish': _print_json(launcher.bus_publish(args.topic, json.loads(args.payload), risk=args.risk))
        elif cmd=='bus-events': _print_json(launcher.bus_events(args.topic, args.limit))
        elif cmd=='bus-dlq': _print_json(launcher.bus_dlq())
        elif cmd=='bus-subscribe': _print_json(launcher.bus_subscribe(args.pattern, args.subscriber))
        elif cmd in ('tool-list','tools'): _print_json(launcher.tool_list(getattr(args,'scope',None)))
        elif cmd=='tool-status': _print_json(launcher.tool_status())
        elif cmd=='tool-execute': _print_json(launcher.tool_execute(args.name, json.loads(args.payload), [s for s in args.scopes.split(',') if s], args.approved))
        elif cmd=='tool-audit': _print_json(launcher.tool_audit())
        elif cmd=='runtime-status': _print_json(launcher.runtime121_status())
        elif cmd=='runtime-start': _print_json(launcher.runtime121_start())
        elif cmd=='runtime-stop': _print_json(launcher.runtime121_stop())
        elif cmd=='runtime-tick': _print_json(launcher.runtime121_tick())
        elif cmd=='runtime-recover': _print_json(launcher.runtime121_recover())
        elif cmd=='runtime-runs': _print_json(launcher.runtime121_runs())
        else: return 2
        return 0
    except Exception as exc:
        print(f'ERROR: {exc}')
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
