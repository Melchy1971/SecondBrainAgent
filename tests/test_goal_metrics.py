from __future__ import annotations

from secondbrain.agent.goals import GoalMetric

from tests._goal_fakes import FakePlanner, make_tracker


def test_metric_increase_progress():
    m = GoalMetric(name="signups", target=100, current=25, baseline=0)
    assert m.progress() == 0.25
    assert m.reached is False


def test_metric_increase_with_baseline():
    m = GoalMetric(name="mrr", target=200, current=150, baseline=100)
    assert m.progress() == 0.5


def test_metric_decrease_progress():
    m = GoalMetric(name="bugs", target=0, current=5, baseline=10, direction="decrease")
    assert m.progress() == 0.5


def test_metric_reached_and_clamped():
    m = GoalMetric(name="x", target=10, current=20, baseline=0)
    assert m.progress() == 1.0
    assert m.reached is True


def test_goal_metric_progress_average(tmp_path):
    tracker, _ = make_tracker(tmp_path)
    goal = tracker.create_goal("Ziel", metrics=[
        {"name": "a", "target": 10, "current": 10},   # 1.0
        {"name": "b", "target": 10, "current": 0},    # 0.0
    ])
    assert tracker.store.get(goal.id).metric_progress() == 0.5


def test_milestone_progress_weighted(tmp_path):
    tracker, _ = make_tracker(tmp_path)
    goal = tracker.create_goal("Ziel", milestones=[
        {"title": "big", "weight": 3},
        {"title": "small", "weight": 1},
    ])
    ms_big = tracker.store.get(goal.id).milestones[0].id
    tracker.complete_milestone(goal.id, ms_big)
    assert tracker.store.get(goal.id).milestone_progress() == 0.75


def test_measure_progress_blends_components(tmp_path):
    planner = FakePlanner(n_steps=2)
    tracker, _ = make_tracker(tmp_path, planner=planner)
    goal = tracker.create_goal("Ziel", metrics=[{"name": "a", "target": 10, "current": 10}])
    tracker.decompose(goal.id)                    # adds 2 milestones + 1 plan
    plan_id = tracker.store.get(goal.id).plan_ids[0]
    planner.complete_all(plan_id)                 # plan fully done
    # complete the milestones too
    for ms in tracker.store.get(goal.id).milestones:
        tracker.complete_milestone(goal.id, ms.id)

    progress = tracker.measure_progress(goal.id)
    assert set(progress.components) == {"milestone", "metric", "plan"}
    assert progress.metric == 1.0
    assert progress.plan == 1.0
    assert progress.milestone == 1.0
    assert progress.overall == 1.0


def test_update_metric_changes_progress(tmp_path):
    tracker, _ = make_tracker(tmp_path)
    goal = tracker.create_goal("Ziel", metrics=[{"name": "signups", "target": 100, "current": 0}])
    assert tracker.measure_progress(goal.id).overall == 0.0
    tracker.update_metric(goal.id, "signups", 50)
    assert tracker.measure_progress(goal.id).overall == 0.5


def test_plan_progress_partial(tmp_path):
    planner = FakePlanner(n_steps=4)
    tracker, _ = make_tracker(tmp_path, planner=planner)
    goal = tracker.create_goal("Ziel")
    tracker.decompose(goal.id)
    plan_id = tracker.store.get(goal.id).plan_ids[0]
    planner.load(plan_id).steps[0].status = "completed"   # 1/4
    # ignore milestone component by measuring plan directly
    assert tracker._plan_progress(tracker.store.get(goal.id)) == 0.25
