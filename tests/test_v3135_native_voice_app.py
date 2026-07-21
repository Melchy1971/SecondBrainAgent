from pathlib import Path

from secondbrain.desktop_native.action_registry import ActionDefinition, build_core_registry
from secondbrain.desktop_native.native_voice_app_gate import run_native_voice_app_gate
from secondbrain.desktop_native.qt_shell import VIEWS, capabilities
from secondbrain.desktop_native.voice_runtime import VoiceSession, VoiceState


def _ready_voice_status():
    return {
        "stt_ready": True,
        "tts_ready": True,
        "stt_policy": {
            "selected_engine": "faster_whisper",
            "faster_whisper_ready": True,
            "vosk_ready": False,
            "windows_speech_ready": False,
            "cloud_opt_in": False,
            "raw_audio_persisted": False,
            "model_download_allowed": False,
        },
        "microphone": {"inventory": {"available": True}},
    }


def test_registry_rejects_duplicate_ids_and_exposes_policy():
    registry = build_core_registry(lambda payload: payload)
    assert registry.get("mail.send").requires_approval is True
    task_create = registry.get("tasks.create")
    assert task_create.risk.value == "write"
    assert task_create.requires_confirmation is True
    assert task_create.requires_workspace is True
    assert registry.resolve_alias("NEUE AUFGABE").id == "tasks.create"
    assert registry.get("tasks.list").requires_workspace is True
    task_complete = registry.get("tasks.complete")
    assert task_complete.requires_confirmation is True
    assert task_complete.requires_workspace is True
    assert registry.resolve_alias("Aufgabe abschließen").id == "tasks.complete"
    task_rename = registry.get("tasks.rename")
    assert task_rename.requires_confirmation is True
    assert task_rename.requires_workspace is True
    assert registry.resolve_alias("AUFGABE UMBENENNEN").id == "tasks.rename"
    task_archive = registry.get("tasks.archive")
    assert task_archive.requires_confirmation is True
    assert task_archive.requires_workspace is True
    assert registry.resolve_alias("AUFGABE ARCHIVIEREN").id == "tasks.archive"
    task_restore = registry.get("tasks.restore")
    assert task_restore.requires_confirmation is True
    assert task_restore.requires_workspace is True
    assert registry.resolve_alias("AUFGABE WIEDERHERSTELLEN").id == "tasks.restore"
    assert registry.get("tasks.filter.all").requires_workspace is True
    assert registry.resolve_alias("ZEIGE OFFENE AUFGABEN").id == "tasks.filter.open"
    assert registry.resolve_alias("AKTIVE AUFGABEN").id == "tasks.filter.open"
    assert registry.resolve_alias("ERLEDIGTE AUFGABEN").id == "tasks.filter.completed"
    assert registry.resolve_alias("ARCHIVIERTE AUFGABEN").id == "tasks.filter.archived"
    assert registry.resolve_alias("  ÖFFNE   DOKUMENTE ").id == "navigation.documents"
    try:
        registry.register(ActionDefinition("mail.send", "duplicate"))
    except ValueError as exc:
        assert "duplicate action id" in str(exc)
    else:
        raise AssertionError("duplicate action was accepted")


def test_free_text_uses_assistant_and_navigation_is_direct():
    calls = []
    session = VoiceSession(build_core_registry(lambda payload: calls.append(payload) or payload))
    navigation = session.understand("öffne dokumente")
    fallback = session.understand("Was fehlt in meinem Wissensbestand?")
    assert navigation["action_id"] == "navigation.documents"
    assert fallback["action_id"] == "assistant.ask"
    assert calls[-1]["text"].startswith("Was fehlt")


def test_confirmation_and_approval_are_payload_and_workspace_bound():
    session = VoiceSession(build_core_registry(lambda payload: payload), workspace_id="alpha")
    assert session.understand("ja")["error"] == "no_bound_confirmation"
    pending = session.understand("sende mail", {"recipient": "a@example.test", "body": "Hallo"})
    assert pending["status"] == "approval_required"
    session.workspace_id = "beta"
    assert session.approve(pending["binding"])["error"] == "approval_binding_mismatch"


def test_multistep_dialog_collects_required_slots_before_approval():
    session = VoiceSession(build_core_registry(lambda payload: payload), workspace_id="alpha")
    first = session.understand("erstelle termin")
    assert first == {"status": "slots_required", "missing": ["title", "when"], "action_id": "calendar.create"}
    second = session.provide_slots({"title": "Arzt"})
    assert second["missing"] == ["when"]
    final = session.provide_slots({"when": "morgen 14 Uhr"})
    assert final["status"] == "approval_required"


def test_wake_word_push_to_talk_and_tts_feedback_guard():
    session = VoiceSession(build_core_registry(lambda payload: payload))
    assert session.push_to_talk() == VoiceState.LISTENING
    session.set_speaking(True)
    assert session.wake("Jarvis") is False
    session.set_speaking(False)
    assert session.wake("Hey Jarvis") is True


def test_qt_shell_is_optional_and_has_required_views():
    result = capabilities()
    assert isinstance(result.degraded_mode, bool)
    assert {"Assistant", "Approvals", "Diagnostics"}.issubset(VIEWS)


def test_native_voice_gate_passes_and_redacts(tmp_path: Path):
    (tmp_path / "SecondBrain" / "desktop_native").mkdir(parents=True)
    (tmp_path / "SecondBrain" / "desktop_native" / "app.py").write_text("", encoding="utf-8")
    report = run_native_voice_app_gate(tmp_path, voice_status=_ready_voice_status())
    assert report["status"] == "PASS"
    assert report["privacy"]["raw_audio_persisted"] is False
    assert report["schema"] == "secondbrain.native_voice_app_gate.v31_79"
    assert len(report["checks"]) == 15
    assert (tmp_path / "runtime" / "reports" / "native_voice_app_gate.json").exists()
