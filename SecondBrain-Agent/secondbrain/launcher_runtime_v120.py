from __future__ import annotations

from pathlib import Path
from typing import Any
import argparse

from .launcher_runtime_v119 import SecondBrainLauncherV119
from .launcher_runtime_v113 import _print_json
from .os_core_v120 import PersonalOSOrchestrator


class SecondBrainLauncherV120(SecondBrainLauncherV119):
    def __init__(self, project_root: str | Path | None = None, profile: str | None = None):
        super().__init__(project_root, profile)
        self.os = PersonalOSOrchestrator(self.config.runtime_dir, self._dispatch_os_action)
        self.workflow_host.register('os.status', lambda payload: self.os_status())
        self.workflow_host.register('os.run', lambda payload: self.os_run(payload.get('objective', ''), bool(payload.get('dry_run', True))))
        self.workflow_host.register('os.manifest', lambda payload: self.os_manifest())

    def _dispatch_os_action(self, action: str, payload: dict[str, Any]) -> Any:
        if action == 'status':
            return self.status()
        if action == 'rag.answer':
            question = payload.get('question') or payload.get('objective') or ''
            return self.rag_answer(question)
        if action == 'agent.run':
            return self.agent_run(payload.get('objective', ''))
        if action == 'workflow.status':
            return self.workflow_status()
        if action == 'twin.status':
            return self.twin_status()
        if action == 'decision.evaluate':
            question = payload.get('question', '')
            return {'question': question, 'note': 'Use decision-evaluate for structured options; v12 dispatch kept read-only by default.'}
        if action == 'ops.release_gate':
            return self.ops_release_gate()
        raise ValueError(f'Unsupported OS action: {action}')

    def os_status(self) -> dict[str, Any]:
        return self.os.status()

    def os_manifest(self) -> dict[str, Any]:
        return self.os.manifest()

    def os_capabilities(self, domain: str | None = None) -> list[dict[str, Any]]:
        return self.os.capabilities.list(domain)

    def os_capability_set_status(self, key: str, status: str) -> dict[str, Any]:
        row = self.os.capabilities.set_status(key, status)
        self.emit('os.capability_status_changed', 'launcher_v120', {'key': key, 'status': status}, risk_level=2)
        return row

    def os_plan(self, objective: str) -> dict[str, Any]:
        return self.os.plan(objective)

    def os_run(self, objective: str, dry_run: bool = False) -> dict[str, Any]:
        row = self.os.run(objective, dry_run=dry_run)
        self.emit('os.run_completed', 'launcher_v120', {'run_id': row['run_id'], 'status': row['status'], 'dry_run': dry_run}, risk_level=2 if dry_run else 3)
        return row

    def os_runs(self, limit: int = 20) -> list[dict[str, Any]]:
        return self.os.runs.list(limit)

    def os_readiness_gate(self) -> dict[str, Any]:
        return self.os.readiness_gate()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='secondbrain', description='SecondBrain OS v12.0 launcher')
    parser.add_argument('--project-root', default=str(Path.cwd()), help='SecondBrain-Agent Projektordner')
    parser.add_argument('--profile', default=None, help='Startprofil, z. B. safe/dev/local-ai')
    sub = parser.add_subparsers(dest='cmd', required=False)
    simple = ['os-status', 'os-manifest', 'os-readiness-gate']
    for cmd in simple:
        sub.add_parser(cmd)
    p_caps = sub.add_parser('os-capabilities'); p_caps.add_argument('--domain', default=None)
    p_cset = sub.add_parser('os-capability-set-status'); p_cset.add_argument('key'); p_cset.add_argument('status')
    p_plan = sub.add_parser('os-plan'); p_plan.add_argument('objective')
    p_run = sub.add_parser('os-run'); p_run.add_argument('objective'); p_run.add_argument('--dry-run', action='store_true')
    p_runs = sub.add_parser('os-runs'); p_runs.add_argument('--limit', type=int, default=20)
    # preserve discoverability for old no-arg commands
    for cmd in ['init','health','sync','tick','start','up','down','status','diagnose','metrics','recover','ops-status','ops-release-gate','ops-health-report','api-status','automation-status','improve-status','mobile-status','voice-status','twin-status','workflow-status']:
        sub.add_parser(cmd)
    return parser


def main(argv: list[str] | None = None) -> int:
    import sys
    raw = list(sys.argv[1:] if argv is None else argv)
    os_cmds = {
        'os-status', 'os-manifest', 'os-readiness-gate', 'os-capabilities',
        'os-capability-set-status', 'os-plan', 'os-run', 'os-runs'
    }
    # Backward compatibility: v12 exposes OS commands, all older launcher commands
    # are delegated before argparse validates the subcommand. This keeps v10.8-v11.9
    # CLI commands operational.
    first_cmd = next((x for x in raw if not x.startswith('-')), None)
    if first_cmd is not None and first_cmd not in os_cmds:
        from .launcher_runtime_v119 import main as legacy_main
        return legacy_main(argv)

    parser = build_parser()
    args, unknown = parser.parse_known_args(argv)
    cmd = args.cmd or 'os-status'
    launcher = SecondBrainLauncherV120(args.project_root, args.profile)
    try:
        if cmd == 'os-status': _print_json(launcher.os_status())
        elif cmd == 'os-manifest': _print_json(launcher.os_manifest())
        elif cmd == 'os-capabilities': _print_json(launcher.os_capabilities(args.domain))
        elif cmd == 'os-capability-set-status': _print_json(launcher.os_capability_set_status(args.key, args.status))
        elif cmd == 'os-plan': _print_json(launcher.os_plan(args.objective))
        elif cmd == 'os-run': _print_json(launcher.os_run(args.objective, args.dry_run))
        elif cmd == 'os-runs': _print_json(launcher.os_runs(args.limit))
        elif cmd == 'os-readiness-gate': _print_json(launcher.os_readiness_gate())
        else:
            from .launcher_runtime_v119 import main as legacy_main
            return legacy_main(argv)
        return 0
    except Exception as exc:
        print(f'ERROR: {exc}')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
