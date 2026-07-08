from __future__ import annotations

from datetime import datetime, timedelta, timezone

from secondbrain.agent.goals import GoalStatus

from tests._goal_fakes import MemorySink, make_tracker


def test_report_creates_and_persists_review(tmp_path):
    tracker, _ = make_tracker(tmp_path)
    goal = tracker.create_goal("Ziel", milestones=[{"title": "M1"}, {"title": "M2"}])
    out = tracker.report(goal.id)
    assert "review" in out and "progress" in out
    stored = tracker.store.reviews(goal.id)
    assert len(stored) == 1
    assert stored[-1].summary


def test_report_sets_at_risk_when_risks_present(tmp_path):
    tracker, _ = make_tracker(tmp_path)
    past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    goal = tracker.create_goal("Ziel", milestones=[{"title": "M1", "due": past}])
    tracker.report(goal.id)
    assert tracker.store.get(goal.id).status == GoalStatus.AT_RISK


def test_report_sets_active_when_no_risks(tmp_path):
    tracker, _ = make_tracker(tmp_path)
    goal = tracker.create_goal("Ziel", milestones=[{"title": "M1"}])
    tracker.report(goal.id)
    assert tracker.store.get(goal.id).status == GoalStatus.ACTIVE


def test_report_notifies_warning_on_risk_info_otherwise(tmp_path):
    tracker, notif = make_tracker(tmp_path)
    past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    goal = tracker.create_goal("Ziel", milestones=[{"title": "M1", "due": past}])
    tracker.report(goal.id)
    assert any(n["level"] == "warning" for n in notif.sent)

    ok_goal = tracker.create_goal("Sauberes Ziel", milestones=[{"title": "M1"}])
    tracker.report(ok_goal.id)
    assert any(n["level"] == "info" for n in notif.sent)


def test_report_feeds_memory_sink(tmp_path):
    mem = MemorySink()
    tracker, _ = make_tracker(tmp_path, memory_sink=mem)
    goal = tracker.create_goal("Ziel")
    tracker.report(goal.id)
    assert any(f["kind"] == "goal_review" for f in mem.facts)


def test_close_notifies_success(tmp_path):
    tracker, notif = make_tracker(tmp_path)
    goal = tracker.create_goal("Ziel")           # no milestones/metrics -> progress 0
    tracker.close(goal.id, force=True)
    assert any(n["level"] == "success" for n in notif.sent)


def test_report_summary_contains_progress(tmp_path):
    tracker, _ = make_tracker(tmp_path)
    goal = tracker.create_goal("Ziel", milestones=[{"title": "M1"}, {"title": "M2"}])
    ms = tracker.store.get(goal.id).milestones[0].id
    tracker.complete_milestone(goal.id, ms)
    out = tracker.report(goal.id)
    assert out["progress"]["overall"] == 0.5
    assert "50%" in out["review"]["summary"]


def test_terminal_goal_status_not_overwritten_by_report(tmp_path):
    tracker, _ = make_tracker(tmp_path)
    goal = tracker.create_goal("Ziel")
    tracker.close(goal.id, force=True)
    tracker.report(goal.id)
    assert tracker.store.get(goal.id).status == GoalStatus.COMPLETED
