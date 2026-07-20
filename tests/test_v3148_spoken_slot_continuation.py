from secondbrain.desktop_native.action_registry import build_core_registry
from secondbrain.desktop_native.action_bus import NativeActionBus
from secondbrain.desktop_native.voice_runtime import VoiceSession, VoiceState


def _session(workspace="alpha"):
    return VoiceSession(build_core_registry(lambda payload: payload), workspace_id=workspace)


def test_follow_up_utterances_fill_one_slot_at_a_time():
    session = _session()
    first = session.understand("erstelle termin")
    assert first["missing"][0] == "title"
    second = session.continue_dialog("Arzt")
    assert second["missing"][0] == "when"
    final = session.continue_dialog("morgen um 14 Uhr")
    assert final["status"] == "approval_required"
    assert session.dialog.parameters == {"title": "Arzt", "when": "morgen um 14 Uhr"}


def test_confirmation_cannot_be_used_as_missing_slot_value():
    session = _session()
    session.understand("erstelle termin")
    result = session.continue_dialog("ja")
    assert result["error"] == "slot_value_required"
    assert session.dialog.missing_parameters == ["title", "when"]


def test_dialog_can_be_cancelled_without_executing_action():
    session = _session()
    session.understand("sende mail")
    result = session.continue_dialog("abbrechen")
    assert result == {"status": "dialog_cancelled", "action_id": "mail.send"}
    assert session.dialog is None
    assert session.state is VoiceState.IDLE


def test_follow_up_is_rejected_after_workspace_change():
    session = _session()
    session.understand("erstelle termin")
    session.workspace_id = "beta"
    assert session.continue_dialog("Arzt")["error"] == "dialog_workspace_mismatch"


def test_explicit_parameters_use_existing_slot_validation():
    session = _session()
    session.understand("erstelle termin")
    result = session.provide_slots({"title": "Arzt"})
    assert result["missing"][0] == "when"


def test_action_bus_routes_spoken_follow_ups_into_one_bound_approval(tmp_path):
    bus = NativeActionBus(tmp_path, workspace_id="alpha")
    assert bus.submit("erstelle termin")["missing"] == ["title", "when"]
    assert bus.submit("Arzt")["missing"] == ["when"]
    result = bus.submit("morgen um 14 Uhr")
    assert result["status"] == "approval_required"
    assert result["approval_id"]
    assert bus.voice.dialog.parameters == {"title": "Arzt", "when": "morgen um 14 Uhr"}
