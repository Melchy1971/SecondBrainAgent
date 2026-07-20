import sys
import threading
from types import SimpleNamespace

from secondbrain.desktop_native.microphone import MicrophoneConfig
from secondbrain.desktop_native.voice_de import GermanVoiceController


class FakeStt:
    def transcribe(self, _audio, _recognizer, *, language):
        return {"ok": True, "engine": "fake", "text": "Hallo", "language": language}

    def status(self):
        return {"selected_engine": "fake"}


def test_parallel_capture_is_rejected_and_active_result_can_be_cancelled(monkeypatch, tmp_path):
    capture_started = threading.Event()
    release_capture = threading.Event()

    class FakeMicrophone:
        def __init__(self, *, device_index):
            self.device_index = device_index

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

    class FakeRecognizer:
        def adjust_for_ambient_noise(self, _source, *, duration):
            return None

        def listen(self, _source, *, timeout, phrase_time_limit):
            capture_started.set()
            assert release_capture.wait(2)
            return object()

    monkeypatch.setitem(
        sys.modules,
        "speech_recognition",
        SimpleNamespace(Recognizer=FakeRecognizer, Microphone=FakeMicrophone),
    )
    controller = GermanVoiceController(
        tmp_path,
        stt_policy=FakeStt(),
        microphone_config=MicrophoneConfig(),
    )
    results = []
    worker = threading.Thread(target=lambda: results.append(controller.listen_once()))
    worker.start()
    assert capture_started.wait(1)
    assert controller.listen_once()["status"] == "busy"
    assert controller.cancel_listening() is True
    release_capture.set()
    worker.join(2)
    assert results[0]["status"] == "cancelled"
    assert controller.status()["listening"] is False
    assert controller.cancel_listening() is False


def test_capture_lock_is_released_after_backend_error(monkeypatch, tmp_path):
    class BrokenMicrophone:
        def __init__(self, *, device_index):
            raise OSError("microphone missing")

    module = SimpleNamespace(Recognizer=lambda: object(), Microphone=BrokenMicrophone)
    monkeypatch.setitem(sys.modules, "speech_recognition", module)
    controller = GermanVoiceController(tmp_path, stt_policy=FakeStt())
    assert controller.listen_once()["ok"] is False
    assert controller.listen_once().get("status") != "busy"
