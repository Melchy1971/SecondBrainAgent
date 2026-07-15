"""Sprint 45 - calendar assistant acceptance tests."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from secondbrain.calendar_assistant.agent import CalendarAgent
from secondbrain.calendar_assistant.gui import CalendarViewModel
from secondbrain.calendar_assistant.models import CalendarEvent, ConflictType, WorkingHours
from secondbrain.calendar_assistant.service import CalendarConnectorError, CalendarService


def _ev(i, s, e, ws="w1", **k):
    return CalendarEvent(event_id=f"ev{i}", calendar_id="c1", workspace_id=ws, title=f"T{i}", start=s, end=e, **k)


def _events():
    return [
        _ev(1, "2026-07-14T10:00:00+00:00", "2026-07-14T11:00:00+00:00"),
        _ev(2, "2026-07-14T14:00:00+00:00", "2026-07-14T15:00:00+00:00"),
        _ev(3, "2026-07-14T09:00:00+00:00", "2026-07-14T09:30:00+00:00", ws="w2"),
    ]


class _Connector:
    def __init__(self):
        self.calls = []

    def create_event(self, payload):
        self.calls.append(payload)
        return {"external_id": "ext-1"}

    def invite_attendees(self, payload):
        self.calls.append(payload)
        return {"invited": True}


class _OfflineConnector:
    def create_event(self, payload):
        raise CalendarConnectorError("offline")


class _ApprovalQueue:
    def __init__(self):
        self.started = set()

    def create(self, **_kwargs):
        return {"approval_id": "appr-1"}

    def begin_execution(self, approval_id, **_kwargs):
        if approval_id in self.started:
            raise RuntimeError("already_executed")
        self.started.add(approval_id)
        return {"approval_id": approval_id, "status": "executing"}


# 1
def test_events_are_read_and_workspace_isolated():
    svc = CalendarService()
    assert [e.title for e in svc.list_events(_events(), workspace_id="w1")] == ["T1", "T2"]
    assert len(svc.list_events(_events(), workspace_id="w2")) == 1


# 2
def test_free_slots_are_correct():
    svc = CalendarService()
    slots = svc.find_free_slots(_events(), period_start="2026-07-14T00:00:00+00:00",
                                period_end="2026-07-14T23:59:00+00:00", duration_minutes=60, working_hours=WorkingHours(), workspace_id="w1")
    starts = [s.start[11:16] for s in slots]
    assert "09:00" in starts and "11:00" in starts and "15:00" in starts
    assert "10:00" not in starts and "14:00" not in starts and "12:00" not in starts  # busy + lunch


# 3
def test_conflicts_detected():
    svc = CalendarService()
    prop = _ev("p", "2026-07-14T10:30:00+00:00", "2026-07-14T11:30:00+00:00")
    types = {c.type for c in svc.detect_conflicts(prop, _events(), working_hours=WorkingHours(), travel_minutes=30, buffer_minutes=15)}
    assert ConflictType.DIRECT_OVERLAP.value in types or ConflictType.DOUBLE_BOOKING.value in types


# 4
def test_create_is_blocked_and_creates_approval():
    class Q:
        def __init__(self): self.created = []
        def create(self, **kw): self.created.append(kw); return {"approval_id": "appr-1"}
    q = Q()
    svc = CalendarService()
    prep = svc.prepare_change("create_event", {"event_id": "", "title": "Neu", "start": "2026-07-15T09:00:00+00:00"},
                              workspace_id="w1", approval_queue=q)
    assert prep["status"] == "approval_required" and prep["approval_id"] == "appr-1"
    assert q.created and q.created[0]["category"] == "connector_permission_change"
    # approval binds event id, payload hash, workspace and expiry
    assert prep["payload_hash"] and prep["expires_at"] and prep["workspace_id"] == "w1"


# 5
def test_approved_create_runs_exactly_once():
    conn = _Connector()
    svc = CalendarService(conn)
    queue = _ApprovalQueue()
    payload = {"event_id": "", "title": "Neu"}
    prep = svc.prepare_change("create_event", payload, workspace_id="w1", approval_queue=queue)
    r1 = svc.commit_change(prep, payload, approval_queue=queue, workspace_id="w1")
    r2 = svc.commit_change(prep, payload, approval_queue=queue, workspace_id="w1")
    assert r1["status"] == "committed"
    assert r2["status"] == "duplicate"
    assert len(conn.calls) == 1


# 6
def test_changed_payload_invalidates_approval():
    svc = CalendarService(_Connector())
    queue = _ApprovalQueue()
    prep = svc.prepare_change("create_event", {"event_id": "", "title": "A"}, workspace_id="w1", approval_queue=queue)
    result = svc.commit_change(prep, {"event_id": "", "title": "B"}, approval_queue=queue, workspace_id="w1")
    assert result["status"] == "invalid" and result["reason"] == "payload_changed"


# 7
def test_timezones_handled():
    svc = CalendarService()
    naive = _ev("n", "2026-07-14T10:30:00", "2026-07-14T11:30:00")
    assert any(c.type == ConflictType.TIMEZONE.value for c in svc.detect_conflicts(naive, _events()))
    # aware event in a different offset is compared correctly (UTC 10:30 == +02:00 12:30)
    plus2 = _ev("z", "2026-07-14T12:30:00+02:00", "2026-07-14T13:30:00+02:00")
    types = {c.type for c in svc.detect_conflicts(plus2, _events())}
    assert ConflictType.DIRECT_OVERLAP.value in types or ConflictType.DOUBLE_BOOKING.value in types


# 8
def test_no_invite_without_approval():
    conn = _Connector()
    svc = CalendarService(conn)
    prep = svc.prepare_change("invite_attendees", {"event_id": "ev1", "attendees": ["a@b.c"]}, workspace_id="w1")
    assert prep["status"] == "approval_required"
    assert conn.calls == []  # nothing sent yet
    assert svc.commit_change(prep, {"event_id": "ev1", "attendees": ["a@b.c"]}, approval_queue=None, workspace_id="w1")["status"] == "blocked"
    assert conn.calls == []


# 9
def test_gui_shows_source_and_status_no_ids():
    vm = CalendarViewModel()
    dv = vm.day_view(_events(), workspace_id="w1", day="2026-07-14T00:00:00+00:00")
    assert dv["events"]
    for item in dv["events"]:
        assert "event_id" not in item and "external_id" not in item
        assert "source" in item and "status" in item
    html = vm.render_html(_events(), workspace_id="w1", day="2026-07-14T00:00:00+00:00")
    assert "ev1" not in html and "KALENDER" in html


# 10
def test_offline_connector_is_controlled_error():
    svc = CalendarService(_OfflineConnector())
    queue = _ApprovalQueue()
    prep = svc.prepare_change("create_event", {"event_id": "", "t": 1}, workspace_id="w1", approval_queue=queue)
    result = svc.commit_change(prep, {"event_id": "", "t": 1}, approval_queue=queue, workspace_id="w1")
    assert result["status"] == "connector_offline"


# agent + expiry
def test_agent_intents_and_expiry():
    agent = CalendarAgent()
    events = _events()
    free = agent.when_free(events, workspace_id="w1", duration_minutes=60,
                           period_start="2026-07-14T00:00:00+00:00", period_end="2026-07-14T23:59:00+00:00",
                           working_hours=WorkingHours())
    assert free["best"] is not None
    move = agent.move_event("ev1", workspace_id="w1", new_start="2026-07-16T09:00:00+00:00", new_end="2026-07-16T10:00:00+00:00")
    assert move["status"] == "approval_required"
    # expired approval is rejected
    svc = CalendarService(_Connector())
    queue = _ApprovalQueue()
    prep = svc.prepare_change("create_event", {"event_id": "", "t": 1}, workspace_id="w1", approval_queue=queue,
                              now=datetime(2026, 1, 1, tzinfo=timezone.utc), ttl_minutes=30)
    late = svc.commit_change(prep, {"event_id": "", "t": 1}, approval_queue=queue, workspace_id="w1", now=datetime(2026, 1, 2, tzinfo=timezone.utc))
    assert late["status"] == "expired"


def test_boolean_approval_bypass_is_impossible_and_workspace_is_bound():
    svc = CalendarService(_Connector())
    queue = _ApprovalQueue()
    payload = {"event_id": "ev1", "title": "Bound"}
    prep = svc.prepare_change("update_event", payload, workspace_id="w1", connector_id="google", approval_queue=queue)
    assert prep["connector_id"] == "google" and prep["idempotency_key"] and prep["attendee_hash"]
    assert svc.commit_change(prep, payload, approval_queue=queue, workspace_id="w2")["reason"] == "workspace_mismatch"


def test_task_link_is_a_user_decision_proposal():
    svc = CalendarService()
    result = svc.link_task("task-1", _events()[0], workspace_id="w1")
    assert result["status"] == "proposed" and result["requires_user_decision"] is True
