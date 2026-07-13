from secondbrain.voice.conversation import ConversationController, State
from secondbrain.voice.engines.fake import FakeStreamingStt, FakeVad, FakeWakeWord, FakeTtsEngine
from secondbrain.voice.ports import Audio


def _wake(): return Audio(b"WAKE")
def _speech(t): return Audio(b"S:" + t.encode())
def _silence(): return Audio(b"-")


def _controller(**kw):
    return ConversationController(
        FakeWakeWord(), FakeVad(), FakeStreamingStt, FakeTtsEngine(),
        responder=lambda text: f"echo:{text}", speaking_frames=2, end_silence_frames=2, **kw)


def test_wake_gates_listening():
    c = _controller()
    assert c.feed(_silence()) == []          # ignored until wake
    assert c.state is State.IDLE
    assert "listening" in c.feed(_wake())
    assert c.state is State.LISTENING


def test_full_turn_wake_listen_think_speak():
    c = _controller(conversation_mode=True)
    events = c.run([_wake(), _speech("hallo"), _silence(), _silence()])
    assert "final" in events and "reply" in events
    assert c.turns[-1] == {"user": "hallo", "assistant": "echo:hallo"}
    assert c.state is State.SPEAKING
    # speaking finishes after speaking_frames of silence -> back to listening
    tail = c.run([_silence(), _silence()])
    assert "spoke" in tail and "listening" in tail
    assert c.state is State.LISTENING


def test_barge_in_interrupts_speaking():
    c = _controller()
    c.run([_wake(), _speech("frage"), _silence(), _silence()])
    assert c.state is State.SPEAKING
    events = c.feed(_speech("stopp"))   # user talks over the assistant
    assert "interrupted" in events and "listening" in events
    assert c.state is State.LISTENING


def test_non_conversation_mode_returns_to_idle():
    c = _controller(conversation_mode=False)
    c.run([_wake(), _speech("x"), _silence(), _silence()])
    tail = c.run([_silence(), _silence()])
    assert "idle" in tail and c.state is State.IDLE
