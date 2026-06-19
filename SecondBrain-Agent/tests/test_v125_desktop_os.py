
from secondbrain.launcher_runtime_v125 import SecondBrainLauncherV125


def test_desktop_status(tmp_path):
    launcher = SecondBrainLauncherV125(tmp_path)
    status = launcher.desktop_status()
    assert status['healthy'] is True
    assert status['widgets']['enabled'] >= 1


def test_desktop_dashboard(tmp_path):
    launcher = SecondBrainLauncherV125(tmp_path)
    snap = launcher.desktop_dashboard()
    assert snap['version'] == '12.5'
    assert 'widgets' in snap
    assert 'commands' in snap


def test_notification_center(tmp_path):
    launcher = SecondBrainLauncherV125(tmp_path)
    row = launcher.desktop_notify('Test', 'Body', 'info')
    assert row['title'] == 'Test'
    assert launcher.desktop_notifications()[0]['notification_id'] == row['notification_id']


def test_command_palette_capture(tmp_path):
    launcher = SecondBrainLauncherV125(tmp_path)
    result = launcher.desktop_command('quick_capture', '{"text":"hello","title":"note"}')
    assert result['result']['status'] == 'captured'


def test_widget_toggle(tmp_path):
    launcher = SecondBrainLauncherV125(tmp_path)
    rows = launcher.desktop_widget_enable('rag_search', False)
    assert any(r['widget_id'] == 'rag_search' and r['enabled'] is False for r in rows)
