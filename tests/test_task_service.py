"""Sprint 44 - task service acceptance tests."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from secondbrain.tasks.models import Status
from secondbrain.tasks.service import (
    DependencyCycleError,
    StatusTransitionError,
    TaskProjectService,
    TaskServiceError,
)


def _svc(tmp_path):
    return TaskProjectService(tmp_path)


def test_create_and_complete(tmp_path):
    s = _svc(tmp_path)
    t = s.create_task(workspace_id="w1", title="A", status="active")
    done = s.complete_task(t.task_id, workspace_id="w1")
    assert done.status == Status.COMPLETED.value
    assert done.completed_at


def test_reopen_and_defer(tmp_path):
    s = _svc(tmp_path)
    t = s.create_task(workspace_id="w1", title="A", status="active")
    s.complete_task(t.task_id, workspace_id="w1")
    assert s.reopen_task(t.task_id, workspace_id="w1").status == Status.ACTIVE.value
    d = s.defer_task(t.task_id, workspace_id="w1", due_date="2026-12-01T00:00:00+00:00")
    assert d.status == Status.WAITING.value and d.due_date.startswith("2026-12-01")


def test_invalid_transition_rejected(tmp_path):
    s = _svc(tmp_path)
    t = s.create_task(workspace_id="w1", title="A", status="active")
    with pytest.raises(StatusTransitionError):
        s.update_task(t.task_id, workspace_id="w1", status="archived")


def test_cycle_is_blocked(tmp_path):
    s = _svc(tmp_path)
    a = s.create_task(workspace_id="w1", title="A")
    b = s.create_task(workspace_id="w1", title="B")
    c = s.create_task(workspace_id="w1", title="C")
    s.add_dependency(a.task_id, b.task_id, workspace_id="w1")
    s.add_dependency(b.task_id, c.task_id, workspace_id="w1")
    with pytest.raises(DependencyCycleError):
        s.add_dependency(c.task_id, a.task_id, workspace_id="w1")


def test_overdue_detected_not_escalated(tmp_path):
    s = _svc(tmp_path)
    past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    over = s.create_task(workspace_id="w1", title="Over", due_date=past, status="active")
    s.create_task(workspace_id="w1", title="Future", due_date=(datetime.now(timezone.utc) + timedelta(days=1)).isoformat())
    overdue = s.get_overdue(workspace_id="w1")
    assert [t.title for t in overdue] == ["Over"]
    # not auto-escalated: status unchanged
    assert s.get_task(over.task_id, workspace_id="w1").status == "active"


def test_completed_predecessor_does_not_block(tmp_path):
    s = _svc(tmp_path)
    a = s.create_task(workspace_id="w1", title="A", status="active")
    b = s.create_task(workspace_id="w1", title="B")
    s.add_dependency(a.task_id, b.task_id, workspace_id="w1")
    assert b.task_id in {t.task_id for t in s.get_blocked(workspace_id="w1")}
    s.complete_task(a.task_id, workspace_id="w1")
    assert b.task_id not in {t.task_id for t in s.get_blocked(workspace_id="w1")}


def test_delete_requires_approval(tmp_path):
    s = _svc(tmp_path)
    t = s.create_task(workspace_id="w1", title="A")
    result = s.delete_task(t.task_id, workspace_id="w1")
    assert result["status"] == "approval_required"
    assert s.get_task(t.task_id, workspace_id="w1") is not None
    # approved delete removes it
    gone = s.delete_task(t.task_id, workspace_id="w1", approved=True)
    assert gone["status"] == "deleted"
    assert s.get_task(t.task_id, workspace_id="w1") is None


def test_source_reference_preserved(tmp_path):
    s = _svc(tmp_path)
    t = s.create_task(workspace_id="w1", title="From mail", source="mail",
                      source_reference="thread:42", confidence=0.8)
    loaded = s.get_task(t.task_id, workspace_id="w1")
    assert loaded.source == "mail" and loaded.source_reference == "thread:42" and loaded.confidence == 0.8


def test_events_are_recorded(tmp_path):
    s = _svc(tmp_path)
    t = s.create_task(workspace_id="w1", title="A", source="agent", confidence=0.6)
    s.complete_task(t.task_id, workspace_id="w1")
    events = s._read("events")  # noqa: SLF001
    types = [e["event_type"] for e in events if e["task_id"] == t.task_id]
    assert "created" in types and "completed" in types
    created = next(e for e in events if e["event_type"] == "created" and e["task_id"] == t.task_id)
    assert created["metadata"]["source"] == "agent" and created["metadata"]["confidence"] == 0.6


def test_workspace_isolation(tmp_path):
    s = _svc(tmp_path)
    s.create_task(workspace_id="w1", title="A")
    s.create_task(workspace_id="w2", title="B")
    assert len(s.list_tasks(workspace_id="w1")) == 1
    assert len(s.list_tasks(workspace_id="w2")) == 1
    assert s.get_overdue(workspace_id="w1") == s.get_overdue(workspace_id="w1")


def test_state_survives_restart(tmp_path):
    s = _svc(tmp_path)
    s.create_task(workspace_id="w1", title="Persisted", status="active")
    reloaded = TaskProjectService(tmp_path)
    assert len(reloaded.list_tasks(workspace_id="w1")) == 1


def test_next_actions_prioritized_and_unblocked(tmp_path):
    s = _svc(tmp_path)
    low = s.create_task(workspace_id="w1", title="low", priority="low")
    crit = s.create_task(workspace_id="w1", title="crit", priority="critical")
    blocked_pred = s.create_task(workspace_id="w1", title="pred")
    blocked = s.create_task(workspace_id="w1", title="blocked", priority="critical")
    s.add_dependency(blocked_pred.task_id, blocked.task_id, workspace_id="w1")
    nxt = s.get_next_actions(workspace_id="w1")
    titles = [t.title for t in nxt]
    assert titles[0] == "crit"
    assert "blocked" not in titles  # blocked by incomplete predecessor
