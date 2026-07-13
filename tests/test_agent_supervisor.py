from __future__ import annotations

from datetime import datetime, timedelta, timezone

from secondbrain.agent.background_agents import AgentFailurePolicy, AgentSchedule, AgentState
from secondbrain.agent.background_agents.models import RUN_FAILED, RUN_SUCCESS
from secondbrain.agent.workflow.store import WorkflowStore

from tests._bg_fakes import make_supervisor


def _failing_agent(sup, action="pause", max_failures=2):
    a = sup.register("Flaky", "import_monitor",
                     failure_policy=AgentFailurePolicy(max_consecutive_failures=max_failures, action=action),
                     config={"force_error": True, "force_error_message": "boom"})
    sup.start(a.id)
    return a


def test_failure_policy_pauses_after_threshold(tmp_path):
    sup, _, notif = make_supervisor(tmp_path)
    a = _failing_agent(sup, action="pause", max_failures=2)

    r1 = sup.run_agent(a.id)
    assert r1.status == RUN_FAILED
    assert sup.store.get_agent(a.id).state == AgentState.ACTIVE
    assert sup.store.get_agent(a.id).consecutive_failures == 1

    r2 = sup.run_agent(a.id)
    assert r2.status == RUN_FAILED
    agent = sup.store.get_agent(a.id)
    assert agent.state == AgentState.PAUSED
    assert agent.consecutive_failures == 2
    assert any(n["level"] == "error" and n["action_required"] for n in notif.sent)


def test_failure_policy_stop_action_marks_failed(tmp_path):
    sup, _, _ = make_supervisor(tmp_path)
    a = _failing_agent(sup, action="stop", max_failures=1)
    sup.run_agent(a.id)
    assert sup.store.get_agent(a.id).state == AgentState.FAILED


def test_success_resets_failure_counter(tmp_path):
    sup, _, _ = make_supervisor(tmp_path)
    a = sup.register("Toggle", "import_monitor",
                     failure_policy=AgentFailurePolicy(max_consecutive_failures=3, action="pause"),
                     config={"force_error": True})
    sup.start(a.id)
    sup.run_agent(a.id)
    assert sup.store.get_agent(a.id).consecutive_failures == 1

    agent = sup.store.get_agent(a.id)
    agent.config = {}
    sup.store.upsert_agent(agent)
    sup.run_agent(a.id)
    assert sup.store.get_agent(a.id).consecutive_failures == 0
    assert sup.store.get_agent(a.id).last_status == RUN_SUCCESS


def test_run_due_respects_interval(tmp_path):
    sup, _, _ = make_supervisor(tmp_path)
    a = sup.register("Ticker", "import_monitor", schedule=AgentSchedule(interval_seconds=3600))
    sup.start(a.id)

    t0 = datetime(2026, 7, 6, 12, 0, tzinfo=timezone.utc)
    first = sup.run_due(now=t0)
    assert len(first) == 1

    soon = sup.run_due(now=t0 + timedelta(minutes=10))
    assert soon == []

    later = sup.run_due(now=t0 + timedelta(minutes=61))
    assert len(later) == 1


def test_run_due_skips_non_active_agents(tmp_path):
    sup, _, _ = make_supervisor(tmp_path)
    sup.register("Paused", "import_monitor", schedule=AgentSchedule(interval_seconds=60))
    assert sup.run_due() == []


def test_run_executes_through_workflow_engine(tmp_path):
    sup, jobs, _ = make_supervisor(tmp_path)
    a = sup.register("WF", "import_monitor")
    sup.start(a.id)
    run = sup.run_agent(a.id)

    cp = WorkflowStore(tmp_path).load(run.workflow_id)
    assert cp is not None
    assert cp.state.value == "COMPLETED"
    assert len(jobs.jobs) == 1
