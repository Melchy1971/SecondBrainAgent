from secondbrain.realtime_voice import RealtimeVoiceRuntime


def test_status(tmp_path):
    rt = RealtimeVoiceRuntime(tmp_path)
    assert rt.status()["version"] == "16.8"


def test_wake_handle(tmp_path):
    rt = RealtimeVoiceRuntime(tmp_path)
    result = rt.wake_and_handle("Jarvis status")
    assert result["ok"] is True
    assert result["result"]["turn"]["status"] == "executed"


def test_no_wake(tmp_path):
    rt = RealtimeVoiceRuntime(tmp_path)
    assert rt.wake_and_handle("status")["ok"] is False


def test_high_risk_approval(tmp_path):
    rt = RealtimeVoiceRuntime(tmp_path)
    result = rt.handle_text("lösche alle daten")
    assert result["turn"]["status"] == "approval_required"


def test_memory_recall(tmp_path):
    rt = RealtimeVoiceRuntime(tmp_path)
    rt.remember("Tischtennis Rückschlag trainieren")
    assert rt.recall("Rückschlag")


def test_interrupt_events(tmp_path):
    rt = RealtimeVoiceRuntime(tmp_path)
    event = rt.interrupt()
    assert event["ok"] is True
    assert rt.events()
