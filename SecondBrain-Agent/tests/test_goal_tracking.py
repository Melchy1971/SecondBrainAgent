from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from secondbrain.agent.goals import GoalStatus

from tests._goal_fakes import FakePlanner, make_tracker


def test_create_goal_active_and_listed(tmp_path):
    tracker, _ = make_tracker(tmp_path)
    goal = tracker.create_goal("SAP Migration abschliessen", description="Q3 Ziel")
    assert goal.status == GoalStatus.ACTIVE
    listed = tracker.list()
    assert len(listed) == 1
    assert listed[0]["id"] == goal.id


def test_decompose_creates_plan_and_milestones(tmp_path):
    planner = FakePlanner(n_steps=3)
    tracker, _ = make_tracker(tmp_path, planner=planner)
    goal = tracker.create_goal("Neues Feature liefern")
    result = tracker.decompose(goal.id)

    assert result["steps"] == 3
    reloaded = tracker.store.get(goal.id)
    assert len(reloaded.plan_ids) == 1
    assert len(reloaded.milestones) == 3               # one milestone per plan step
    assert any(e.ref.startswith("plan:") for e in reloaded.evidence)


def test_decompose_without_planner_raises(tmp_path):
    tracker, _ = make_tracker(tmp_path, planner=None)
    goal = tracker.create_goal("Ziel ohne Planner")
    with pytest.raises(RuntimeError):
        tracker.decompose(goal.id)


def test_complete_milestone_advances_progress(tmp_path):
    tracker, _ = make_tracker(tmp_path)
    goal = tracker.create_goal("Ziel", milestones=[{"title": "M1"}, {"title": "M2"}])
    before = tracker.measure_progress(goal.id).overall
    ms_id = tracker.store.get(goal.id).milestones[0].id
    tracker.complete_milestone(goal.id, ms_id)
    after = tracker.measure_progress(goal.id).overall
    assert after > before
    assert after == 0.5


def test_pause_and_resume(tmp_path):
    tracker, _ = make_tracker(tmp_path)
    goal = tracker.create_goal("Ziel")
    assert tracker.pause(goal.id).status == GoalStatus.PAUSED
    assert tracker.resume(goal.id).status == GoalStatus.ACTIVE


def test_close_requires_full_progress_unless_forced(tmp_path):
    tracker, _ = make_tracker(tmp_path)
    goal = tracker.create_goal("Ziel", milestones=[{"title": "M1"}, {"title": "M2"}])
    with pytest.raises(ValueError):
        tracker.close(goal.id)
    # force closes anyway
    assert tracker.close(goal.id, force=True).status == GoalStatus.COMPLETED


def test_close_after_all_milestones_done(tmp_path):
    tracker, _ = make_tracker(tmp_path)
    goal = tracker.create_goal("Ziel", milestones=[{"title": "M1"}])
    ms_id = tracker.store.get(goal.id).milestones[0].id
    tracker.complete_milestone(goal.id, ms_id)
    assert tracker.close(goal.id).status == GoalStatus.COMPLETED


def test_risks_flags_overdue_milestone(tmp_path):
    tracker, _ = make_tracker(tmp_path)
    past = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    goal = tracker.create_goal("Ziel", milestones=[{"title": "M1", "due": past}])
    risks = tracker.risks(goal.id)
    assert any(r.startswith("milestone_overdue") for r in risks)


def test_paused_goal_is_a_risk(tmp_path):
    tracker, _ = make_tracker(tmp_path)
    goal = tracker.create_goal("Ziel")
    tracker.pause(goal.id)
    assert "goal_paused" in tracker.risks(goal.id)


def test_unknown_goal_raises(tmp_path):
    tracker, _ = make_tracker(tmp_path)
    with pytest.raises(KeyError):
        tracker.measure_progress("nope")


def test_dashboard_snapshot_aggregates(tmp_path):
    tracker, _ = make_tracker(tmp_path)
    tracker.create_goal("A")
    b = tracker.create_goal("B")
    tracker.pause(b.id)
    snap = tracker.dashboard_snapshot()
    assert snap["total"] == 2
    assert snap["by_status"]["ACTIVE"] == 1
    assert b.id in snap["at_risk"]           # paused counts as at-risk
