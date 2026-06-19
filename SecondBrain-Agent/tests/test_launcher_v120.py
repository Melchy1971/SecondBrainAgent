from secondbrain.launcher_runtime_v120 import SecondBrainLauncherV120


def test_launcher_v120_status(tmp_path):
    root = tmp_path / 'project'
    root.mkdir()
    (root / 'secondbrain').mkdir()
    (root / 'launcher.py').write_text('x=1', encoding='utf-8')
    launcher = SecondBrainLauncherV120(root)
    status = launcher.os_status()
    assert status['version'] == '12.0'
    assert status['capabilities_total'] >= 12


def test_launcher_v120_plan(tmp_path):
    root = tmp_path / 'project'
    root.mkdir()
    (root / 'secondbrain').mkdir()
    (root / 'launcher.py').write_text('x=1', encoding='utf-8')
    launcher = SecondBrainLauncherV120(root)
    plan = launcher.os_plan('Release Health prüfen')
    assert plan['max_risk_level'] >= 1
