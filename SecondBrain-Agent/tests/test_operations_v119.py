
from pathlib import Path
import zipfile

from secondbrain.operations_v119 import OperationsEngine, BackupManager, ReleaseGate, MigrationManager


def test_backup_create_and_verify(tmp_path):
    root = tmp_path / 'project'; runtime = tmp_path / 'runtime'
    (root / 'secondbrain').mkdir(parents=True)
    (root / 'launcher.py').write_text('print("ok")', encoding='utf-8')
    (root / 'requirements.txt').write_text('', encoding='utf-8')
    engine = OperationsEngine(root, runtime)
    backup = engine.create_backup(label='test')
    assert Path(backup['path']).exists()
    result = engine.backups.verify(backup['backup_id'])
    assert result['zip_ok'] is True
    assert result['manifest_ok'] is True


def test_release_gate_status(tmp_path):
    root = tmp_path / 'project'; runtime = tmp_path / 'runtime'
    (root / 'secondbrain').mkdir(parents=True)
    (root / 'launcher.py').write_text('x=1', encoding='utf-8')
    (root / 'requirements.txt').write_text('', encoding='utf-8')
    gate = ReleaseGate(root, runtime).run()
    assert gate['status'] in {'PASS', 'CONDITIONAL_PASS'}
    assert gate['failures'] == 0


def test_migration_plan_and_marker(tmp_path):
    mgr = MigrationManager(tmp_path / 'project', tmp_path / 'runtime')
    plan = mgr.plan('12.0')
    assert plan['ready'] is False
    mgr.apply_marker('v119_backup_gate', 'ok')
    state = mgr.status()
    assert any(x['id'] == 'v119_backup_gate' for x in state['applied'])


def test_restore_plan_safe(tmp_path):
    root = tmp_path / 'project'; runtime = tmp_path / 'runtime'
    root.mkdir(); (root / 'launcher.py').write_text('x=1', encoding='utf-8'); (root / 'secondbrain').mkdir()
    mgr = BackupManager(root, runtime)
    backup = mgr.create()
    plan = mgr.restore_plan(backup['backup_id'])
    assert plan['safe_restore_only'] is True
    assert 'restore_' in plan['target_dir']
