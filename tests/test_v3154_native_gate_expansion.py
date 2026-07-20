import json

from secondbrain.desktop_native.native_voice_app_gate import run_native_voice_app_gate


def _voice_status(*, ready):
    return {
        "stt_ready": ready,
        "tts_ready": ready,
        "stt_policy": {
            "selected_engine": "vosk" if ready else "none",
            "faster_whisper_ready": False,
            "vosk_ready": ready,
            "windows_speech_ready": False,
            "cloud_opt_in": False,
            "raw_audio_persisted": False,
            "model_download_allowed": False,
        },
        "microphone": {"inventory": {"available": ready}},
    }


def test_expanded_gate_replaces_placeholder_groups_with_real_checks(tmp_path):
    native = tmp_path / "SecondBrain" / "desktop_native"
    native.mkdir(parents=True)
    (native / "app.py").write_text("", encoding="utf-8")
    report = run_native_voice_app_gate(tmp_path, voice_status=_voice_status(ready=True))
    assert report["status"] == "PASS"
    assert report["blocked"] == []
    assert report["metrics"]["navigation_views"] == 18
    assert {item["name"] for item in report["checks"]} == {
        "application_shell", "service_integration", "voice_input", "voice_output", "wake_word",
        "intent_coverage", "dialog_state", "confirmation", "approval", "privacy",
        "workspace_isolation", "recovery", "windows_integration", "accessibility", "performance",
    }


def test_written_gate_report_is_redacted_and_omits_local_report_path(tmp_path):
    native = tmp_path / "SecondBrain" / "desktop_native"
    native.mkdir(parents=True)
    (native / "app.py").write_text("", encoding="utf-8")
    report = run_native_voice_app_gate(tmp_path, voice_status=_voice_status(ready=True))
    persisted = json.loads((tmp_path / "runtime" / "reports" / "native_voice_app_gate.json").read_text(encoding="utf-8"))
    assert "report_path" not in persisted
    assert "redacted@example.invalid" not in repr(persisted)
    assert report["report_path"].endswith("native_voice_app_gate.json")


def test_gate_reports_missing_live_voice_runtime_as_conditional(tmp_path):
    native = tmp_path / "SecondBrain" / "desktop_native"
    native.mkdir(parents=True)
    (native / "app.py").write_text("", encoding="utf-8")

    report = run_native_voice_app_gate(
        tmp_path,
        write_report=False,
        voice_status=_voice_status(ready=False),
    )

    assert report["status"] == "CONDITIONAL_PASS"
    assert report["blocked"] == []
    assert report["warnings"] == ["voice_input", "voice_output", "wake_word"]
    assert report["readiness"] == {
        "stt_ready": False,
        "tts_ready": False,
        "microphone_available": False,
        "selected_stt_engine": "none",
        "faster_whisper_ready": False,
        "vosk_ready": False,
        "windows_speech_ready": False,
    }


def test_gate_does_not_treat_unsupported_edge_tts_as_local_runtime(tmp_path):
    native = tmp_path / "SecondBrain" / "desktop_native"
    native.mkdir(parents=True)
    (native / "app.py").write_text("", encoding="utf-8")
    voice_status = _voice_status(ready=True)
    voice_status["modules"] = {"pyttsx3": False, "edge_tts": True}

    report = run_native_voice_app_gate(tmp_path, write_report=False, voice_status=voice_status)

    assert report["status"] == "CONDITIONAL_PASS"
    assert report["warnings"] == ["voice_output"]
    assert report["readiness"]["tts_ready"] is False
