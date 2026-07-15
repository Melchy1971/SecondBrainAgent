
from __future__ import annotations

from pathlib import Path
from typing import Any
import argparse

from .launcher_runtime_v118 import SecondBrainLauncherV118
from .launcher_runtime_v113 import _print_json
from .operations_v119 import OperationsEngine


class SecondBrainLauncherV119(SecondBrainLauncherV118):
    def __init__(self, project_root: str | Path | None = None, profile: str | None = None):
        super().__init__(project_root, profile)
        self.operations = OperationsEngine(self.project_root, self.config.runtime_dir)
        self.workflow_host.register('ops.status', lambda payload: self.ops_status())
        self.workflow_host.register('ops.backup', lambda payload: self.ops_backup(bool(payload.get('include_runtime', True)), payload.get('label')))
        self.workflow_host.register('ops.release_gate', lambda payload: self.ops_release_gate())

    def ops_status(self) -> dict[str, Any]:
        return self.operations.status()

    def ops_backup(
        self,
        include_runtime: bool = True,
        label: str | None = None,
        *,
        encrypt: bool | None = None,
        include_database: bool = True,
    ) -> dict[str, Any]:
        row = self.operations.create_backup(
            include_runtime,
            label,
            encrypt=encrypt,
            include_database=include_database,
        )
        self.emit('operations.backup_created', 'launcher_v119', {'backup_id': row['backup_id'], 'path': row['path']}, risk_level=2)
        return row

    def ops_backups(self, limit: int = 20) -> list[dict[str, Any]]:
        return self.operations.backups.list(limit)

    def ops_backup_verify(self, backup: str) -> dict[str, Any]:
        return self.operations.backups.verify(backup)

    def ops_restore_plan(self, backup: str, target_dir: str | None = None) -> dict[str, Any]:
        return self.operations.restore_wizard.dry_run(backup, target_dir)

    def ops_restore(self, backup: str, target_dir: str | None = None) -> dict[str, Any]:
        row = self.operations.restore_wizard.restore(backup, target_dir)
        self.emit('operations.backup_restored_to_separate_folder', 'launcher_v119', {'backup': backup, 'target_dir': row['target_dir']}, risk_level=3)
        return row

    def ops_restore_rollback(self) -> dict[str, Any]:
        row = self.operations.restore_wizard.rollback()
        self.emit('operations.restore_rolled_back', 'launcher_v119', {'status': row['status']}, risk_level=3)
        return row

    def ops_backup_health(self) -> dict[str, Any]:
        return self.operations.backup_health()

    def ops_backup_report(self) -> dict[str, Any]:
        return self.operations.backup_report()

    def ops_backup_schedule_configure(self, interval: str, enabled: bool) -> dict[str, Any]:
        return self.operations.backup_scheduler.configure(interval=interval, enabled=enabled)

    def ops_backup_schedule_run(self) -> dict[str, Any]:
        return self.operations.scheduled_backup()

    def ops_release_gate(self) -> dict[str, Any]:
        return self.operations.release_gate()

    def ops_migration_plan(self, target_version: str = '12.0') -> dict[str, Any]:
        return self.operations.migrations.plan(target_version)

    def ops_migration_mark(self, migration_id: str, note: str = '') -> dict[str, Any]:
        row = self.operations.migrations.apply_marker(migration_id, note)
        self.emit('operations.migration_marked', 'launcher_v119', {'migration_id': migration_id}, risk_level=2)
        return row

    def ops_health_report(self) -> dict[str, Any]:
        return self.operations.health_report()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='secondbrain', description='SecondBrain OS v11.9 launcher')
    parser.add_argument('--project-root', default=str(Path.cwd()), help='SecondBrain-Agent Projektordner')
    parser.add_argument('--profile', default=None, help='Startprofil, z. B. safe/dev/local-ai')
    sub = parser.add_subparsers(dest='cmd', required=False)
    base_cmds = ['init','health','sync','tick','start','rag-index','agent-status','up','down','status','restart','diagnose','metrics','recover','workflow-status','twin-status','decision-history','voice-status','voice-session','voice-sessions','mobile-status','mobile-devices','mobile-push-list','mobile-captures','mobile-approvals','api-status','api-manifest','api-token-list','api-audit','automation-status','automation-tasks','improve-status','improve-analyze','improve-report','ops-status','ops-release-gate','ops-health-report','ops-backup-health','ops-backup-report','ops-backup-schedule-run','ops-restore-rollback']
    for cmd in base_cmds:
        sub.add_parser(cmd)
    p_b = sub.add_parser('ops-backup'); p_b.add_argument('--no-runtime', action='store_true'); p_b.add_argument('--label', default=None); p_b.add_argument('--unencrypted-dev', action='store_true'); p_b.add_argument('--no-database', action='store_true')
    p_bl = sub.add_parser('ops-backups'); p_bl.add_argument('--limit', type=int, default=20)
    p_v = sub.add_parser('ops-backup-verify'); p_v.add_argument('backup')
    p_rp = sub.add_parser('ops-restore-plan'); p_rp.add_argument('backup'); p_rp.add_argument('--target-dir', default=None)
    p_rs = sub.add_parser('ops-restore'); p_rs.add_argument('backup'); p_rs.add_argument('--target-dir', default=None)
    p_sc = sub.add_parser('ops-backup-schedule-configure'); p_sc.add_argument('--interval', choices=['hourly', 'daily', 'weekly'], default='daily'); p_sc.add_argument('--disabled', action='store_true')
    p_mp = sub.add_parser('ops-migration-plan'); p_mp.add_argument('--target-version', default='12.0')
    p_mm = sub.add_parser('ops-migration-mark'); p_mm.add_argument('migration_id'); p_mm.add_argument('--note', default='')
    # v11.8 passthrough commands
    p_fb = sub.add_parser('improve-feedback'); p_fb.add_argument('source'); p_fb.add_argument('target_type'); p_fb.add_argument('target_id'); p_fb.add_argument('rating', type=int); p_fb.add_argument('--text', default=''); p_fb.add_argument('--tags', default='')
    p_bl2 = sub.add_parser('improve-backlog'); p_bl2.add_argument('--status', default=None); p_bl2.add_argument('--limit', type=int, default=30)
    p_set = sub.add_parser('improve-set-status'); p_set.add_argument('item_id'); p_set.add_argument('status')
    p_rec = sub.add_parser('improve-recommend'); p_rec.add_argument('--limit', type=int, default=5)
    p_reg = sub.add_parser('improve-regression'); p_reg.add_argument('--current', default='{}'); p_reg.add_argument('--baseline', default='{}')
    p_gui = sub.add_parser('gui'); p_gui.add_argument('--snapshot', action='store_true')
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args, unknown = parser.parse_known_args(argv)
    cmd = args.cmd or 'status'
    launcher = SecondBrainLauncherV119(args.project_root, args.profile)
    try:
        if cmd == 'ops-status': _print_json(launcher.ops_status())
        elif cmd == 'ops-backup': _print_json(launcher.ops_backup(not args.no_runtime, args.label, encrypt=False if args.unencrypted_dev else None, include_database=not args.no_database))
        elif cmd == 'ops-backups': _print_json(launcher.ops_backups(args.limit))
        elif cmd == 'ops-backup-verify': _print_json(launcher.ops_backup_verify(args.backup))
        elif cmd == 'ops-restore-plan': _print_json(launcher.ops_restore_plan(args.backup, args.target_dir))
        elif cmd == 'ops-restore': _print_json(launcher.ops_restore(args.backup, args.target_dir))
        elif cmd == 'ops-restore-rollback': _print_json(launcher.ops_restore_rollback())
        elif cmd == 'ops-backup-health': _print_json(launcher.ops_backup_health())
        elif cmd == 'ops-backup-report': _print_json(launcher.ops_backup_report())
        elif cmd == 'ops-backup-schedule-configure': _print_json(launcher.ops_backup_schedule_configure(args.interval, not args.disabled))
        elif cmd == 'ops-backup-schedule-run': _print_json(launcher.ops_backup_schedule_run())
        elif cmd == 'ops-release-gate': _print_json(launcher.ops_release_gate())
        elif cmd == 'ops-migration-plan': _print_json(launcher.ops_migration_plan(args.target_version))
        elif cmd == 'ops-migration-mark': _print_json(launcher.ops_migration_mark(args.migration_id, args.note))
        elif cmd == 'ops-health-report': _print_json(launcher.ops_health_report())
        else:
            from .launcher_runtime_v118 import main as legacy_main
            return legacy_main(argv)
        return 0
    except Exception as exc:
        print(f'ERROR: {exc}')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
