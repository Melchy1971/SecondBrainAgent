from datetime import datetime
from zoneinfo import ZoneInfo

from secondbrain.desktop_native.action_bus import NativeActionBus
from secondbrain.desktop_native.calendar_time_de import resolve_german_calendar_time


BERLIN = ZoneInfo("Europe/Berlin")


def _now(value: str) -> datetime:
    return datetime.fromisoformat(value).replace(tzinfo=BERLIN)


def test_relative_german_times_resolve_in_configured_timezone():
    now = _now("2026-07-21T10:00:00")

    assert resolve_german_calendar_time("heute um 14 Uhr", now=now) == _now("2026-07-21T14:00:00")
    assert resolve_german_calendar_time("morgen 9:30 Uhr", now=now) == _now("2026-07-22T09:30:00")
    assert resolve_german_calendar_time("uebermorgen um 18.15 Uhr", now=now) == _now("2026-07-23T18:15:00")
    assert resolve_german_calendar_time("übermorgen um 18:15 Uhr", now=now) == _now("2026-07-23T18:15:00")


def test_explicit_german_date_and_aware_iso_are_supported():
    now = _now("2026-07-21T10:00:00")
    iso = "2026-07-24T08:00:00+02:00"

    assert resolve_german_calendar_time("24.07.2026 um 8 Uhr", now=now) == _now("2026-07-24T08:00:00")
    assert resolve_german_calendar_time(iso, now=now).isoformat() == iso


def test_ambiguous_or_nonexistent_dst_times_are_never_guessed():
    spring = _now("2026-03-28T12:00:00")
    autumn = _now("2026-10-24T12:00:00")

    assert resolve_german_calendar_time("morgen um 2:30 Uhr", now=spring) is None
    assert resolve_german_calendar_time("morgen um 2:30 Uhr", now=autumn) is None


def test_ambiguous_words_past_times_and_invalid_zones_are_rejected():
    now = _now("2026-07-21T10:00:00")

    assert resolve_german_calendar_time("morgen um zwei", now=now) is None
    assert resolve_german_calendar_time("heute um 9 Uhr", now=now) is None
    assert resolve_german_calendar_time("morgen 14", now=now) is None
    assert resolve_german_calendar_time("morgen um 14 Uhr", now=now, timezone_name="Invalid/Zone") is None


def test_timezone_can_be_overridden_via_environment(monkeypatch):
    monkeypatch.setenv("SECONDBRAIN_CALENDAR_TIMEZONE", "UTC")

    resolved = resolve_german_calendar_time("morgen um 14 Uhr", now=_now("2026-07-21T10:00:00"))

    assert resolved == datetime.fromisoformat("2026-07-22T14:00:00+00:00")


def test_unresolved_time_reopens_bound_slot_without_creating_approval(tmp_path):
    bus = NativeActionBus(tmp_path, workspace_id="alpha")

    first = bus.submit("erstelle termin", {"title": "Arzt", "when": "morgen um zwei"})

    assert first == {
        "status": "slots_required",
        "missing": ["when"],
        "action_id": "calendar.create",
        "error": "calendar_time_unresolved",
    }
    assert bus.approvals.list() == []
    assert bus.voice.dialog.parameters == {"title": "Arzt"}


def test_corrected_time_creates_one_normalized_approval(tmp_path, monkeypatch):
    resolved = _now("2026-07-22T14:00:00")
    monkeypatch.setattr(
        "secondbrain.desktop_native.action_bus.resolve_german_calendar_time",
        lambda value: None if "zwei" in value else resolved,
    )
    bus = NativeActionBus(tmp_path, workspace_id="alpha")
    bus.submit("erstelle termin", {"title": "Arzt", "when": "morgen um zwei"})

    result = bus.submit("morgen um 14 Uhr")

    assert result["status"] == "approval_required"
    row = bus.approvals.get(result["approval_id"])
    execution = row["payload"]["execution_payload"]
    assert execution["start"] == "2026-07-22T14:00:00+02:00"
    assert execution["end"] == "2026-07-22T15:00:00+02:00"
    assert len(bus.approvals.list()) == 1
