from secondbrain.voice_companion import VoiceCompanion


def test_status(tmp_path):
    vc = VoiceCompanion(tmp_path)
    assert vc.status()["version"] == "13.5"


def test_wake_word_detected(tmp_path):
    vc = VoiceCompanion(tmp_path)
    result = vc.wake_and_handle("Jarvis status")
    assert result["ok"] is True
    assert result["wake"]["detected"] is True


def test_wake_word_missing(tmp_path):
    vc = VoiceCompanion(tmp_path)
    result = vc.wake_and_handle("status")
    assert result["ok"] is False


def test_risky_command_requires_approval(tmp_path):
    vc = VoiceCompanion(tmp_path)
    turn = vc.conversation.handle_text("lösche alle daten")
    assert turn["execution"]["status"] == "approval_required"


def test_memory_recall(tmp_path):
    vc = VoiceCompanion(tmp_path)
    vc.memory.remember("Jarvis merkt sich Tischtennis")
    assert vc.memory.recall("Tischtennis")


def test_interrupt(tmp_path):
    vc = VoiceCompanion(tmp_path)
    event = vc.conversation.interrupt()
    assert event["type"] == "interrupt"
