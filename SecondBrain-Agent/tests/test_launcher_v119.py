
from secondbrain.launcher_runtime_v119 import SecondBrainLauncherV119


def test_launcher_ops_status(tmp_path):
    launcher = SecondBrainLauncherV119(project_root=tmp_path)
    status = launcher.ops_status()
    assert status['version'] == '11.9'
    assert 'release_gate' in status


def test_launcher_ops_backup(tmp_path):
    (tmp_path / 'launcher.py').write_text('x=1', encoding='utf-8')
    (tmp_path / 'secondbrain').mkdir(exist_ok=True)
    launcher = SecondBrainLauncherV119(project_root=tmp_path)
    row = launcher.ops_backup(label='unit')
    assert row['backup_id'].startswith('backup_')
    assert launcher.ops_backup_verify(row['backup_id'])['zip_ok'] is True
