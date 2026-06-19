from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any
import argparse
import json

from .launcher_runtime_v108 import SecondBrainLauncher, main as legacy_main, _print_json
from .runtime_manager_v111 import RuntimeManager
from .gui_v111 import run_tk_dashboard, write_dashboard_snapshot


class SecondBrainLauncherV111(SecondBrainLauncher):
    def __init__(self, project_root: str | Path | None = None, profile: str | None = None):
        super().__init__(project_root, profile)
        self.runtime_manager = RuntimeManager(self.project_root, self)

    def up(self) -> dict[str, Any]:
        return self.runtime_manager.start()

    def down(self) -> dict[str, Any]:
        return self.runtime_manager.stop()

    def runtime_status(self) -> dict[str, Any]:
        return self.runtime_manager.status()

    def restart_runtime(self) -> dict[str, Any]:
        return self.runtime_manager.restart()

    def diagnose(self) -> dict[str, Any]:
        return self.runtime_manager.diagnose()

    def metrics(self) -> dict[str, Any]:
        return self.runtime_manager.metrics()

    def recover(self) -> dict[str, Any]:
        return self.runtime_manager.recover()

    def gui(self, snapshot: bool = False) -> Any:
        if snapshot:
            return str(write_dashboard_snapshot(self.runtime_manager))
        return run_tk_dashboard(self.runtime_manager)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog='secondbrain', description='SecondBrain OS v11.1 launcher')
    parser.add_argument('--project-root', default=str(Path.cwd()), help='SecondBrain-Agent Projektordner')
    parser.add_argument('--profile', default=None, help='Startprofil, z. B. safe/dev/local-ai')
    sub = parser.add_subparsers(dest='cmd', required=False)

    for cmd in ['init','health','sync','tick','start','rag-index','agent-status']:
        sub.add_parser(cmd)
    for cmd in ['up','down','status','restart','diagnose','metrics','recover']:
        sub.add_parser(cmd)

    p_gui = sub.add_parser('gui')
    p_gui.add_argument('--snapshot', action='store_true')

    p_rag_search = sub.add_parser('rag-search')
    p_rag_search.add_argument('query')
    p_rag_search.add_argument('--limit', type=int, default=8)

    p_rag_answer = sub.add_parser('rag-answer')
    p_rag_answer.add_argument('query')
    p_rag_answer.add_argument('--limit', type=int, default=5)
    p_rag_answer.add_argument('--write', action='store_true')

    p_agent_run = sub.add_parser('agent-run')
    p_agent_run.add_argument('objective')
    p_agent_run.add_argument('--max-steps', type=int, default=5)

    p_loop = sub.add_parser('loop')
    p_loop.add_argument('--interval', type=int, default=30)
    p_loop.add_argument('--max-cycles', type=int, default=None)

    p_ask = sub.add_parser('ask')
    p_ask.add_argument('prompt')
    p_ask.add_argument('--task', default='default')
    p_ask.add_argument('--provider', default=None)

    p_capture = sub.add_parser('capture')
    p_capture.add_argument('text')
    p_capture.add_argument('--title', default='Quick Capture')

    p_notify = sub.add_parser('notify')
    p_notify.add_argument('message')
    p_notify.add_argument('--severity', default='info')

    p_submit = sub.add_parser('submit')
    p_submit.add_argument('action')
    p_submit.add_argument('payload', nargs='?', default='{}', help='JSON payload')

    args = parser.parse_args(argv)
    launcher = SecondBrainLauncherV111(args.project_root, args.profile)
    cmd = args.cmd or 'status'

    try:
        if cmd == 'init':
            _print_json(launcher.init_runtime())
        elif cmd == 'health':
            _print_json(launcher.health())
        elif cmd == 'sync':
            _print_json([asdict(r) for r in launcher.sync_connectors()])
        elif cmd == 'tick':
            _print_json(launcher.tick())
        elif cmd == 'start':
            _print_json(launcher.start_once())
        elif cmd == 'up':
            _print_json(launcher.up())
        elif cmd == 'down':
            _print_json(launcher.down())
        elif cmd == 'status':
            _print_json(launcher.runtime_status())
        elif cmd == 'restart':
            _print_json(launcher.restart_runtime())
        elif cmd == 'diagnose':
            _print_json(launcher.diagnose())
        elif cmd == 'metrics':
            _print_json(launcher.metrics())
        elif cmd == 'recover':
            _print_json(launcher.recover())
        elif cmd == 'gui':
            result = launcher.gui(snapshot=args.snapshot)
            if result not in (None, 0): print(result)
        elif cmd == 'rag-index':
            _print_json(launcher.rag_index())
        elif cmd == 'agent-status':
            _print_json(launcher.autonomous_status())
        elif cmd == 'rag-search':
            _print_json(launcher.rag_search(args.query, args.limit))
        elif cmd == 'rag-answer':
            if args.write:
                print(launcher.rag_write_answer(args.query, args.limit))
            else:
                _print_json(launcher.rag_answer(args.query, args.limit))
        elif cmd == 'agent-run':
            _print_json(launcher.autonomous_run(args.objective, args.max_steps))
        elif cmd == 'loop':
            launcher.start_loop(args.interval, args.max_cycles)
        elif cmd == 'ask':
            print(launcher.ask(args.prompt, args.task, args.provider))
        elif cmd == 'capture':
            print(launcher.quick_capture(args.text, args.title))
        elif cmd == 'notify':
            print(launcher.notify(args.message, args.severity))
        elif cmd == 'submit':
            _print_json(asdict(launcher.submit(args.action, json.loads(args.payload))))
        else:
            return legacy_main(argv)
        return 0
    except Exception as exc:
        print(f'ERROR: {exc}')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
