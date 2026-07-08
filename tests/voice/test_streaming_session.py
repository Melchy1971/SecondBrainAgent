from secondbrain.voice.streaming import StreamingSttSession
from secondbrain.voice.engines.fake import FakeStreamingStt, FakeVad
from secondbrain.voice.ports import Audio, Transcript


def _speech(t): return Audio(b"S:" + t.encode())
def _silence(): return Audio(b"-")


def test_endpoints_on_trailing_silence():
    session = StreamingSttSession(FakeStreamingStt, FakeVad(), end_silence_frames=2)
    assert session.feed(_speech("hallo"))["partials"] == ["hallo"]
    assert session.feed(_speech("welt"))["partials"] == ["hallo welt"]
    assert session.feed(_silence())["final"] is None       # 1 silence frame, not yet endpointed
    final = session.feed(_silence())["final"]               # 2nd silence -> endpoint
    assert isinstance(final, Transcript) and final.text == "hallo welt"


def test_session_resets_between_utterances():
    session = StreamingSttSession(FakeStreamingStt, FakeVad(), end_silence_frames=1)
    session.feed(_speech("one")); first = session.feed(_silence())["final"]
    session.feed(_speech("two")); second = session.feed(_silence())["final"]
    assert first.text == "one" and second.text == "two"
