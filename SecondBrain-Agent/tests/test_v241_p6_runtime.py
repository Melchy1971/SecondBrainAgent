from secondbrain.voice.vad import VoiceActivityDetector
from secondbrain.voice.session_manager import VoiceSessionManager
from secondbrain.gates.p6_completion_report import build_p6_completion_report


def test_vad():
    assert VoiceActivityDetector().detect([0.0, 0.2])


def test_session_manager():
    manager = VoiceSessionManager()
    manager.start("s1")
    assert manager.get("s1").active


def test_completion_report():
    report = build_p6_completion_report()
    assert report["next_phase"] == "P7_MOBILE"
