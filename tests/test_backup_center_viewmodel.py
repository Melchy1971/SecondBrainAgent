from __future__ import annotations

import base64
import os

from secondbrain.desktop_native.app import NAV_ITEMS
from secondbrain.gui.backup_center import BackupCenterViewModel
from secondbrain.launcher_runtime_v119 import build_parser
from secondbrain.operations_v119 import OperationsEngine


def _key_env() -> dict[str, str]:
    return {
        **os.environ,
        "SECONDBRAIN_BACKUP_KEY": base64.b64encode(b"b" * 32).decode("ascii"),
    }


def test_backup_center_exposes_history_health_and_restore_dry_run(tmp_path):
    project = tmp_path / "project"
    runtime = project / "runtime"
    (project / "config").mkdir(parents=True)
    (project / "config" / "app.json").write_text('{"mode":"test"}', encoding="utf-8")
    operations = OperationsEngine(project, runtime, env=_key_env())
    model = BackupCenterViewModel(project, runtime, operations=operations)

    empty = model.snapshot()
    assert empty["backup_center"]["backup_count"] == 0
    assert empty["restore_center"]["status"] == "NOT_STARTED"

    created = model.create_backup(label="gui", include_database=False, encrypt=True)
    snapshot = model.snapshot()
    assert snapshot["backup_center"]["backup_count"] == 1
    assert snapshot["history"][0]["backup_id"] == created["backup_id"]
    assert model.validate_backup(created["backup_id"])["ok"] is True
    dry_run = model.restore_dry_run(created["backup_id"])
    assert dry_run["status"] == "READY"
    assert dry_run["dry_run"] is True


def test_native_navigation_and_launcher_expose_backup_workflows():
    assert "Backups" in NAV_ITEMS
    parser = build_parser()
    assert parser.parse_args(["ops-backup-health"]).cmd == "ops-backup-health"
    assert parser.parse_args(["ops-backup-schedule-configure", "--interval", "weekly"]).interval == "weekly"
    assert parser.parse_args(["ops-restore-rollback"]).cmd == "ops-restore-rollback"

