import sys
from types import SimpleNamespace

from secondbrain.desktop_native.microphone import MicrophoneConfig, MicrophoneInventory
from secondbrain.desktop_native.voice_de import GermanVoiceController


def test_microphone_config_reads_device_and_bounded_capture_values():
    config = MicrophoneConfig.from_environ(
        {
            "SECONDBRAIN_MICROPHONE_DEVICE_INDEX": "2",
            "SECONDBRAIN_MICROPHONE_CALIBRATION_SECONDS": "99",
            "SECONDBRAIN_MICROPHONE_TIMEOUT_SECONDS": "0",
            "SECONDBRAIN_MICROPHONE_PHRASE_LIMIT_SECONDS": "12.5",
        }
    )
    assert config.device_index == 2
    assert config.calibration_seconds == 5.0
    assert config.timeout_seconds == 0.1
    assert config.phrase_time_limit_seconds == 12.5


def test_invalid_environment_values_fall_back_without_blocking_startup():
    config = MicrophoneConfig.from_environ(
        {
            "SECONDBRAIN_MICROPHONE_DEVICE_INDEX": "invalid",
            "SECONDBRAIN_MICROPHONE_TIMEOUT_SECONDS": "invalid",
        }
    )
    assert config.device_index is None
    assert config.timeout_seconds == 5.0


def test_inventory_lists_devices_and_validates_selection():
    module = SimpleNamespace(Microphone=SimpleNamespace(list_microphone_names=lambda: ["Desk Mic", "Headset"]))
    inventory = MicrophoneInventory(module_loader=lambda _name: module)
    assert inventory.status(1)["available"] is True
    assert inventory.status(1)["devices"][1] == {"index": 1, "name": "Headset"}
    assert inventory.status(5)["selected_available"] is False


def test_inventory_reports_missing_dependency_as_degraded_mode():
    def missing(_name):
        raise ImportError("audio backend missing")

    status = MicrophoneInventory(module_loader=missing).status()
    assert status["available"] is False
    assert status["devices"] == []
    assert "audio backend missing" in status["error"]


def test_controller_passes_selected_device_and_calibration_to_backend(monkeypatch, tmp_path):
    calls = {}

    class FakeMicrophone:
        def __init__(self, *, device_index):
            calls["device_index"] = device_index

        def __enter__(self):
            return object()

        def __exit__(self, *_args):
            return None

    class FakeRecognizer:
        def adjust_for_ambient_noise(self, _source, *, duration):
            calls["calibration"] = duration

        def listen(self, _source, *, timeout, phrase_time_limit):
            calls["capture"] = (timeout, phrase_time_limit)
            return object()

    class FakeStt:
        def transcribe(self, _audio, _recognizer, *, language):
            return {"ok": True, "engine": "fake", "text": "Hallo", "language": language}

        def status(self):
            return {"selected_engine": "fake"}

    monkeypatch.setitem(
        sys.modules,
        "speech_recognition",
        SimpleNamespace(Recognizer=FakeRecognizer, Microphone=FakeMicrophone),
    )
    controller = GermanVoiceController(
        tmp_path,
        stt_policy=FakeStt(),
        microphone_config=MicrophoneConfig(3, 0.7, 4.0, 9.0),
    )
    result = controller.listen_once()
    assert result["ok"] is True
    assert calls == {"device_index": 3, "calibration": 0.7, "capture": (4.0, 9.0)}
