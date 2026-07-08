
from __future__ import annotations

from pathlib import Path
from typing import Any
import argparse
import json

from .launcher_runtime_v117 import SecondBrainLauncherV117
from .launcher_runtime_v113 import _print_json
from .self_improvement_v118 import SelfImprovementEngine


class SecondBrainLauncherV118(SecondBrainLauncherV117):
    def __init__(self, project_root: str | Path | None = None, profile: str | None = None):
        super().__init__(project_root, profile)
        self.improvement = SelfImprovementEngine(self.config.runtime_dir)
        self.workflow_host.register('improve.status', lambda payload: self.improve_status())
        self.workflow_host.register('improve.analyze', lambda payload: self.improve_analyze())
        self.workflow_host.register('improve.recommend', lambda payload: self.improve_recommend(int(payload.get('limit', 5))))

    def improve_status(self) -> dict[str, Any]:
        return self.improvement.status()

    def improve_feedback(self, source: str, target_type: str, target_id: str, rating: int, text: str = '', tags: list[str] | None = None) -> dict[str, Any]:
        row = self.improvement.record_feedback(source, target_type, target_id, rating, text, tags or [])
        self.emit('improvement.feedback_recorded', 'launcher_v118', {'feedback_id': row['feedback_id'], 'rating': rating}, risk_level=1)
        return row

    def improve_backlog(self, status: str | None = None, limit: int = 30) -> list[dict[str, Any]]:
        return self.improvement.backlog(status, limit)

    def improve_set_status(self, item_id: str, status: str) -> dict[str, Any]:
        row = self.improvement.set_item_status(item_id, status)
        self.emit('improvement.item_status_changed', 'launcher_v118', {'item_id': item_id, 'status': status}, risk_level=2)
        return row

    def improve_analyze(self) -> dict[str, Any]:
        return self.improvement.analyze_runs()

    def improve_regression(self, current: dict[str, Any], baseline: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.improvement.detect_regressions(current, baseline)

    def improve_recommend(self, limit: int = 5) -> list[dict[str, Any]]:
        return self.improvement.recommend_next(limit)

    def improve_report(self) -> dict[str, Any]:
        return self.improvement.export_report()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='secondbrain', description='SecondBrain OS v11.8 launcher')
    parser.add_argument('--project-root', default=str(Path.cwd()), help='SecondBrain-Agent Projektordner')
    parser.add_argument('--profile', default=None, help='Startprofil, z. B. safe/dev/local-ai')
    sub = parser.add_subparsers(dest='cmd', required=False)
    base_cmds = ['init','health','sync','tick','start','rag-index','agent-status','up','down','status','restart','diagnose','metrics','recover','workflow-status','twin-status','decision-history','voice-status','voice-session','voice-sessions','mobile-status','mobile-devices','mobile-push-list','mobile-captures','mobile-approvals','api-status','api-manifest','api-token-list','api-audit','automation-status','automation-tasks','improve-status','improve-analyze','improve-report']
    for cmd in base_cmds:
        sub.add_parser(cmd)
    p_fb = sub.add_parser('improve-feedback'); p_fb.add_argument('source'); p_fb.add_argument('target_type'); p_fb.add_argument('target_id'); p_fb.add_argument('rating', type=int); p_fb.add_argument('--text', default=''); p_fb.add_argument('--tags', default='')
    p_bl = sub.add_parser('improve-backlog'); p_bl.add_argument('--status', default=None); p_bl.add_argument('--limit', type=int, default=30)
    p_set = sub.add_parser('improve-set-status'); p_set.add_argument('item_id'); p_set.add_argument('status')
    p_rec = sub.add_parser('improve-recommend'); p_rec.add_argument('--limit', type=int, default=5)
    p_reg = sub.add_parser('improve-regression'); p_reg.add_argument('--current', default='{}'); p_reg.add_argument('--baseline', default='{}')
    # passthrough v11.7/v11.6 commands
    p_runs = sub.add_parser('automation-runs'); p_runs.add_argument('--limit', type=int, default=30); p_runs.add_argument('--task-id', default=None)
    p_every = sub.add_parser('automation-every'); p_every.add_argument('name'); p_every.add_argument('target'); p_every.add_argument('--minutes', type=int, default=60); p_every.add_argument('--payload', default='{}'); p_every.add_argument('--max-runs', type=int, default=None)
    p_once = sub.add_parser('automation-once'); p_once.add_argument('name'); p_once.add_argument('target'); p_once.add_argument('--run-at', default=None); p_once.add_argument('--payload', default='{}')
    p_run = sub.add_parser('automation-run'); p_run.add_argument('task_id')
    p_due = sub.add_parser('automation-run-due'); p_due.add_argument('--limit', type=int, default=10)
    p_en = sub.add_parser('automation-enable'); p_en.add_argument('task_id')
    p_dis = sub.add_parser('automation-disable'); p_dis.add_argument('task_id')
    p_api_tok = sub.add_parser('api-token-create'); p_api_tok.add_argument('name'); p_api_tok.add_argument('--scopes', default='read:status')
    p_api_call = sub.add_parser('api-dispatch'); p_api_call.add_argument('method'); p_api_call.add_argument('path'); p_api_call.add_argument('--payload', default='{}'); p_api_call.add_argument('--token', default=None); p_api_call.add_argument('--internal', action='store_true')
    p_api_srv = sub.add_parser('api-serve'); p_api_srv.add_argument('--host', default='127.0.0.1'); p_api_srv.add_argument('--port', type=int, default=8765)
    p_gui = sub.add_parser('gui'); p_gui.add_argument('--snapshot', action='store_true')
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args, unknown = parser.parse_known_args(argv)
    cmd = args.cmd or 'status'
    launcher = SecondBrainLauncherV118(args.project_root, args.profile)
    try:
        if cmd == 'improve-status': _print_json(launcher.improve_status())
        elif cmd == 'improve-feedback': _print_json(launcher.improve_feedback(args.source, args.target_type, args.target_id, args.rating, args.text, [x.strip() for x in args.tags.split(',') if x.strip()]))
        elif cmd == 'improve-backlog': _print_json(launcher.improve_backlog(args.status, args.limit))
        elif cmd == 'improve-set-status': _print_json(launcher.improve_set_status(args.item_id, args.status))
        elif cmd == 'improve-analyze': _print_json(launcher.improve_analyze())
        elif cmd == 'improve-regression': _print_json(launcher.improve_regression(json.loads(args.current), json.loads(args.baseline) if args.baseline else None))
        elif cmd == 'improve-recommend': _print_json(launcher.improve_recommend(args.limit))
        elif cmd == 'improve-report': _print_json(launcher.improve_report())
        else:
            from .launcher_runtime_v117 import main as legacy_main
            return legacy_main(argv)
        return 0
    except Exception as exc:
        print(f'ERROR: {exc}')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
