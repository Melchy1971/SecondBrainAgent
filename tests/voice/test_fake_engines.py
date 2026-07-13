from secondbrain.voice.engines.fake import FakeTtsEngine, FakeStreamingStt
from secondbrain.voice.ports import Audio, AudioClip, Transcript


def test_fake_tts_returns_audioclip():
    clip = FakeTtsEngine().synthesize("hallo")
    assert isinstance(clip, AudioClip)
    assert clip.data.startswith(b"RIFF") and clip.sample_rate == 22050


def test_fake_streaming_accumulates_then_final():
    stream = FakeStreamingStt()
    assert stream.push(Audio(b"S:hello")) == ["hello"]
    assert stream.push(Audio(b"S:world")) == ["hello world"]
    final = stream.finalize()
    assert isinstance(final, Transcript) and final.text == "hello world"
