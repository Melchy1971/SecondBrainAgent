from pathlib import Path

from secondbrain.desktop_native.stt import LocalSttPolicy


class FakeRecognizer:
    def __init__(self) -> None:
        self.google_calls = 0

    def recognize_google(self, audio, *, language):
        self.google_calls += 1
        return "Cloud text"

    def recognize_vosk(self, audio):
        return '{"text": "lokaler text"}'


def test_cloud_stt_is_blocked_without_explicit_opt_in():
    policy = LocalSttPolicy(environ={}, module_available=lambda _name: False)
    recognizer = FakeRecognizer()
    result = policy.transcribe(object(), recognizer)
    assert result["ok"] is False
    assert recognizer.google_calls == 0
    assert policy.status()["raw_audio_persisted"] is False


def test_cloud_stt_requires_explicit_true_value():
    policy = LocalSttPolicy(
        environ={"SECONDBRAIN_CLOUD_STT_OPT_IN": "true"},
        module_available=lambda _name: False,
    )
    recognizer = FakeRecognizer()
    result = policy.transcribe(object(), recognizer)
    assert result == {"ok": True, "engine": "google", "text": "Cloud text"}
    assert recognizer.google_calls == 1


def test_vosk_has_priority_over_opted_in_cloud(tmp_path: Path, monkeypatch):
    model_path = tmp_path / "vosk-model"
    model_path.mkdir()
    class FakeDecoder:
        def __init__(self, model, rate): pass
        def AcceptWaveform(self, data): return True
        def FinalResult(self): return '{"text": "lokaler text"}'
    class FakeAudio:
        def get_raw_data(self, **kwargs): return b"audio"
    import sys
    import types
    monkeypatch.setitem(sys.modules, "vosk", types.SimpleNamespace(Model=lambda path: path, KaldiRecognizer=FakeDecoder))
    policy = LocalSttPolicy(
        environ={"SECONDBRAIN_CLOUD_STT_OPT_IN": "true", "SECONDBRAIN_VOSK_MODEL_PATH": str(model_path)},
        module_available=lambda name: name == "vosk",
    )
    recognizer = FakeRecognizer()
    result = policy.transcribe(FakeAudio(), recognizer)
    assert result["engine"] == "vosk"
    assert result["text"] == "lokaler text"
    assert recognizer.google_calls == 0


def test_whisper_requires_existing_local_model_directory(tmp_path: Path):
    missing = tmp_path / "not-downloaded"
    policy = LocalSttPolicy(
        environ={"SECONDBRAIN_WHISPER_MODEL_PATH": str(missing)},
        module_available=lambda name: name == "faster_whisper",
    )
    assert policy.status()["selected_engine"] == "none"
    assert policy.status()["model_download_allowed"] is False
