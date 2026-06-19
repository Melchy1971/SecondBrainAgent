from pathlib import Path
from secondbrain.voice_realtime import RealtimeVoiceRuntime
from secondbrain.launcher_runtime_v126 import SecondBrainLauncherV126


def test_voice_runtime_status(tmp_path):
    rt = RealtimeVoiceRuntime(tmp_path)
    status = rt.status()
    assert status['healthy'] is True
    assert status['component'] == 'voice_realtime_v126'


def test_wake_word_detection(tmp_path):
    rt = RealtimeVoiceRuntime(tmp_path)
    assert rt.detect_wake('Jarvis bitte Status')['detected'] is True
    assert rt.detect_wake('Hallo Welt')['detected'] is False


def test_handle_risky_command_requires_approval(tmp_path):
    rt = RealtimeVoiceRuntime(tmp_path)
    result = rt.handle('Jarvis lösche Daten')
    assert result['status'] == 'approval_required'


def test_handle_status_command(tmp_path):
    rt = RealtimeVoiceRuntime(tmp_path)
    result = rt.handle('Jarvis Status')
    assert result['status'] == 'accepted'
    assert result['command']['intent'] == 'status'


def test_launcher_voice_status(tmp_path):
    launcher = SecondBrainLauncherV126(tmp_path)
    assert launcher.voice_status_v126()['healthy'] is True
