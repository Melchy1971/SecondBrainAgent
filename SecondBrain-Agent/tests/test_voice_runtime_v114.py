from pathlib import Path

from secondbrain.voice_runtime_v114 import VoiceRuntime
from secondbrain.launcher_runtime_v114 import SecondBrainLauncherV114


def test_voice_status_defaults(tmp_path: Path):
    runtime = VoiceRuntime(tmp_path)
    status = runtime.status()
    assert status["version"] == "11.4"
    assert status["wake_word"] == "jarvis"


def test_voice_router_extracts_capture_intent(tmp_path: Path):
    runtime = VoiceRuntime(tmp_path)
    parsed = runtime.parse("Jarvis notiz Testeintrag speichern")
    assert parsed["intent"] == "capture.note"
    assert "Testeintrag" in parsed["args"]["text"]


def test_voice_blocks_risky_agent_without_approval(tmp_path: Path):
    runtime = VoiceRuntime(tmp_path, executor=lambda command: {"status": "executed"})
    result = runtime.handle_text("Jarvis agent Plane mein Projekt")
    assert result["blocked"] is True
    assert result["executed"] is False


def test_voice_executes_safe_command(tmp_path: Path):
    runtime = VoiceRuntime(tmp_path, executor=lambda command: {"status": "ok", "intent": command.intent})
    result = runtime.handle_text("Jarvis status")
    assert result["blocked"] is False
    assert result["executed"] is True
    assert result["result"]["intent"] == "runtime.status"


def test_launcher_voice_status(tmp_path: Path):
    launcher = SecondBrainLauncherV114(project_root=tmp_path)
    status = launcher.voice_status()
    assert status["version"] == "11.4"
