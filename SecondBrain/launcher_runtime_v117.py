
from __future__ import annotations

from pathlib import Path
from typing import Any
import argparse
import json

from .launcher_runtime_v116 import SecondBrainLauncherV116
from .launcher_runtime_v113 import _print_json
from .automation_scheduler_v117 import AutomationScheduler


class SecondBrainLauncherV117(SecondBrainLauncherV116):
    def __init__(self, project_root: str | Path | None = None, profile: str | None = None):
        super().__init__(project_root, profile)
        self.automation = AutomationScheduler(self.config.runtime_dir, self)
        self.workflow_host.register('automation.status', lambda payload: self.automation_status())
        self.workflow_host.register('automation.run_due', lambda payload: self.automation_run_due(int(payload.get('limit', 10))))

    def automation_status(self) -> dict[str, Any]:
        return self.automation.status()

    def automation_tasks(self) -> list[dict[str, Any]]:
        return self.automation.list_tasks()

    def automation_runs(self, limit: int = 30, task_id: str | None = None) -> list[dict[str, Any]]:
        return self.automation.list_runs(limit, task_id)

    def automation_every(self, name: str, target: str, every_minutes: int, payload: dict[str, Any] | None = None, max_runs: int | None = None) -> dict[str, Any]:
        task = self.automation.create_interval(name, target, payload or {}, every_minutes, max_runs)
        self.emit('automation.task_created', 'launcher_v117', {'task_id': task['task_id'], 'target': target}, risk_level=2)
        return task

    def automation_once(self, name: str, target: str, payload: dict[str, Any] | None = None, run_at: str | None = None) -> dict[str, Any]:
        task = self.automation.create_once(name, target, payload or {}, run_at)
        self.emit('automation.task_created', 'launcher_v117', {'task_id': task['task_id'], 'target': target}, risk_level=2)
        return task

    def automation_enable(self, task_id: str) -> dict[str, Any]:
        return self.automation.set_enabled(task_id, True)

    def automation_disable(self, task_id: str) -> dict[str, Any]:
        return self.automation.set_enabled(task_id, False)

    def automation_run_due(self, limit: int = 10) -> dict[str, Any]:
        return self.automation.run_due(limit)

    def automation_run(self, task_id: str) -> dict[str, Any]:
        return self.automation.run_task(task_id)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='secondbrain', description='SecondBrain OS v11.7 launcher')
    parser.add_argument('--project-root', default=str(Path.cwd()), help='SecondBrain-Agent Projektordner')
    parser.add_argument('--profile', default=None, help='Startprofil, z. B. safe/dev/local-ai')
    sub = parser.add_subparsers(dest='cmd', required=False)
    base_cmds = ['init','health','sync','tick','start','rag-index','agent-status','up','down','status','restart','diagnose','metrics','recover','workflow-status','twin-status','decision-history','voice-status','voice-session','voice-sessions','mobile-status','mobile-devices','mobile-push-list','mobile-captures','mobile-approvals','api-status','api-manifest','api-token-list','api-audit','automation-status','automation-tasks']
    for cmd in base_cmds:
        sub.add_parser(cmd)
    p_runs = sub.add_parser('automation-runs'); p_runs.add_argument('--limit', type=int, default=30); p_runs.add_argument('--task-id', default=None)
    p_every = sub.add_parser('automation-every'); p_every.add_argument('name'); p_every.add_argument('target'); p_every.add_argument('--minutes', type=int, default=60); p_every.add_argument('--payload', default='{}'); p_every.add_argument('--max-runs', type=int, default=None)
    p_once = sub.add_parser('automation-once'); p_once.add_argument('name'); p_once.add_argument('target'); p_once.add_argument('--run-at', default=None); p_once.add_argument('--payload', default='{}')
    p_run = sub.add_parser('automation-run'); p_run.add_argument('task_id')
    p_due = sub.add_parser('automation-run-due'); p_due.add_argument('--limit', type=int, default=10)
    p_en = sub.add_parser('automation-enable'); p_en.add_argument('task_id')
    p_dis = sub.add_parser('automation-disable'); p_dis.add_argument('task_id')
    # v11.6 commands
    p_api_tok = sub.add_parser('api-token-create'); p_api_tok.add_argument('name'); p_api_tok.add_argument('--scopes', default='read:status')
    p_api_call = sub.add_parser('api-dispatch'); p_api_call.add_argument('method'); p_api_call.add_argument('path'); p_api_call.add_argument('--payload', default='{}'); p_api_call.add_argument('--token', default=None); p_api_call.add_argument('--internal', action='store_true')
    p_api_srv = sub.add_parser('api-serve'); p_api_srv.add_argument('--host', default='127.0.0.1'); p_api_srv.add_argument('--port', type=int, default=8765)
    p_gui = sub.add_parser('gui'); p_gui.add_argument('--snapshot', action='store_true')
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args, unknown = parser.parse_known_args(argv)
    cmd = args.cmd or 'status'
    launcher = SecondBrainLauncherV117(args.project_root, args.profile)
    try:
        if cmd == 'automation-status': _print_json(launcher.automation_status())
        elif cmd == 'automation-tasks': _print_json(launcher.automation_tasks())
        elif cmd == 'automation-runs': _print_json(launcher.automation_runs(args.limit, args.task_id))
        elif cmd == 'automation-every': _print_json(launcher.automation_every(args.name, args.target, args.minutes, json.loads(args.payload), args.max_runs))
        elif cmd == 'automation-once': _print_json(launcher.automation_once(args.name, args.target, json.loads(args.payload), args.run_at))
        elif cmd == 'automation-run': _print_json(launcher.automation_run(args.task_id))
        elif cmd == 'automation-run-due': _print_json(launcher.automation_run_due(args.limit))
        elif cmd == 'automation-enable': _print_json(launcher.automation_enable(args.task_id))
        elif cmd == 'automation-disable': _print_json(launcher.automation_disable(args.task_id))
        elif cmd in {'api-status','api-manifest','api-token-create','api-token-list','api-audit','api-dispatch','api-serve'}:
            from .launcher_runtime_v116 import main as legacy_main
            return legacy_main(argv)
        else:
            from .launcher_runtime_v116 import main as legacy_main
            return legacy_main(argv)
        return 0
    except Exception as exc:
        print(f'ERROR: {exc}')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
