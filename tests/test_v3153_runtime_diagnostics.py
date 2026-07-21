from secondbrain.desktop_native.runtime_diagnostics import runtime_diagnostics, safe_status


def _snapshot(*, external_actions=None, **voice_overrides):
    voice = {
        "language": "de-DE",
        "stt_ready": True,
        "tts_ready": True,
        "listening": False,
        "stt_policy": {"selected_engine": "vosk", "cloud_opt_in": False, "raw_audio_persisted": False},
        "microphone": {"inventory": {"available": True, "selected_index": 1, "selected_available": True}},
        **voice_overrides,
    }
    return runtime_diagnostics(
        voice=voice,
        voice_state="IDLE",
        wake={"enabled": True, "running": True, "local_only": True, "raw_audio_persisted": False},
        hotkey={"enabled": True, "available": True, "running": True, "raw_keys_recorded": False},
        tray_running=True,
        approvals={"available": True, "pending_count": 2, "elevated_count": 1, "overdue_count": 1},
        jobs={"running_count": 1, "blocked_count": 3},
        approval_config={"notifications_enabled": False, "overdue_minutes": 30, "refresh_seconds": 5},
        external_actions=external_actions,
    )


def test_ready_runtime_exposes_only_operational_summary():
    snapshot = _snapshot()
    assert snapshot["status"] == "ready"
    assert snapshot["components"]["jobs"] == {"running_count": 1, "blocked_count": 3}
    assert snapshot["components"]["approvals"] == {
        "available": True,
        "pending_count": 2,
        "elevated_count": 1,
        "overdue_count": 1,
        "notifications_enabled": False,
        "overdue_minutes": 30,
        "refresh_seconds": 5,
    }


def test_approval_diagnostics_use_safe_defaults_without_config():
    snapshot = runtime_diagnostics(
        voice={},
        voice_state="IDLE",
        wake={},
        hotkey={},
        tray_running=False,
        approvals={},
        jobs={},
    )
    assert snapshot["components"]["approvals"] == {
        "available": False,
        "pending_count": 0,
        "elevated_count": 0,
        "overdue_count": 0,
        "notifications_enabled": True,
        "overdue_minutes": 15,
        "refresh_seconds": 2,
    }
    assert snapshot["components"]["external_actions"] == {
        "provider": "disabled",
        "configured": False,
        "authenticated": False,
        "calendar_write": False,
        "mail_write": False,
        "reason": "disabled",
    }


def test_external_action_diagnostics_expose_readiness_without_secrets():
    snapshot = _snapshot(external_actions={
        "provider": "google",
        "configured": True,
        "authenticated": True,
        "calendar_write": True,
        "mail_write": True,
        "reason": "ready",
        "access_token": "must-not-appear",
    })

    assert snapshot["components"]["external_actions"] == {
        "provider": "google",
        "configured": True,
        "authenticated": True,
        "calendar_write": True,
        "mail_write": True,
        "reason": "ready",
    }
    assert "must-not-appear" not in repr(snapshot)


def test_missing_microphone_or_stt_reports_degraded_without_blocking():
    snapshot = _snapshot(
        stt_ready=False,
        microphone={"inventory": {"available": False, "error": "device missing"}},
    )
    assert snapshot["status"] == "degraded"
    assert snapshot["components"]["microphone"]["available"] is False


def test_diagnostics_drops_secrets_paths_payloads_and_device_names():
    snapshot = _snapshot(
        api_key="super-secret",
        model_path="C:/private/model",
        microphone={"inventory": {"available": True, "devices": [{"name": "Private Desk Mic"}]}},
        payload={"mail": "secret@example.test"},
    )
    rendered = repr(snapshot)
    assert "super-secret" not in rendered
    assert "C:/private" not in rendered
    assert "Private Desk Mic" not in rendered
    assert "secret@example.test" not in rendered
    assert snapshot["privacy"] == {
        "secrets_exposed": False,
        "payloads_exposed": False,
        "device_names_exposed": False,
        "local_paths_exposed": False,
    }


def test_failing_component_is_isolated_without_error_details():
    def broken():
        raise RuntimeError("C:/private/queue.jsonl contains secret")

    assert safe_status(broken) == {}
