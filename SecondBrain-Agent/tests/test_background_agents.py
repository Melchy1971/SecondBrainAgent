from __future__ import annotations

import pytest

from secondbrain.agent.background_agents import AgentSchedule, AgentState, AgentType
from secondbrain.agent.background_agents.models import RUN_FAILED, RUN_SKIPPED, RUN_SUCCESS

from tests._bg_fakes import FakeJobs, MemorySink, make_supervisor


def test_register_and_list(tmp_path):
    sup, _, _ = make_supervisor(tmp_path)
    agent = sup.register("Import Waechter", "import_monitor",
                         schedule=AgentSchedule(interval_seconds=3600))
    assert agent.state == AgentState.REGISTERED
    listed = sup.list()
    assert len(listed) == 1
    assert listed[0]["id"] == agent.id
    assert listed[0]["agent_type"] == "import_monitor"


def test_lifecycle_transitions(tmp_path):
    sup, _, _ = make_supervisor(tmp_path)
    a = sup.register("A", "system_health_agent")
    assert sup.start(a.id).state == AgentState.ACTIVE
    assert sup.pause(a.id).state == AgentState.PAUSED
    assert sup.stop(a.id).state == AgentState.STOPPED
    assert sup.resume(a.id).state == AgentState.ACTIVE


def test_run_requires_active_state(tmp_path):
    sup, _, _ = make_supervisor(tmp_path)
    a = sup.register("A", "import_monitor")
    run = sup.run_agent(a.id)
    assert run.status == RUN_SKIPPED
    assert "agent_not_active" in run.error


def test_run_import_monitor_success_records_run(tmp_path):
    sup, jobs, _ = make_supervisor(tmp_path)
    a = sup.register("Import", "import_monitor")
    sup.start(a.id)
    run = sup.run_agent(a.id)
    assert run.status == RUN_SUCCESS
    assert run.output["checked"] == "import_jobs"
    assert run.workflow_id
    runs = sup.runs(a.id)
    assert runs[-1]["run_id"] == run.run_id
    assert any(status == "success" for _, status in jobs.status_calls)


@pytest.mark.parametrize("agent_type", [t.value for t in AgentType])
def test_all_builtin_agent_types_run(tmp_path, agent_type):
    mem = MemorySink()
    sup, jobs, notif = make_supervisor(tmp_path, memory_sink=mem)
    a = sup.register(f"Agent {agent_type}", agent_type)
    sup.start(a.id)
    run = sup.run_agent(a.id)
    assert run.status == RUN_SUCCESS
    assert run.output["ok"] is True


def test_memory_consolidation_uses_memory_sink(tmp_path):
    mem = MemorySink()
    sup, _, _ = make_supervisor(tmp_path, memory_sink=mem)
    a = sup.register("Memory", "memory_consolidation")
    sup.start(a.id)
    run = sup.run_agent(a.id)
    assert run.output["memory_delivered"] is True
    assert any(f["kind"] == "memory_consolidation" for f in mem.facts)


def test_notification_agent_emits_notification(tmp_path):
    sup, _, notif = make_supervisor(tmp_path)
    a = sup.register("Digest", "notification_agent")
    sup.start(a.id)
    sup.run_agent(a.id)
    assert any(n["category"] == "agent" for n in notif.sent)


def test_system_health_agent_flags_degraded_queue(tmp_path):
    jobs = FakeJobs(snapshot_health="blocked")
    sup, _, notif = make_supervisor(tmp_path, jobs=jobs)
    a = sup.register("Health", "system_health_agent")
    sup.start(a.id)
    run = sup.run_agent(a.id)
    assert run.output["healthy"] is False
    assert any(n["level"] == "warning" for n in notif.sent)


def test_unknown_agent_raises(tmp_path):
    sup, _, _ = make_supervisor(tmp_path)
    with pytest.raises(KeyError):
        sup.run_agent("nope")


def test_invalid_agent_type_raises(tmp_path):
    sup, _, _ = make_supervisor(tmp_path)
    with pytest.raises(ValueError):
        sup.register("Bad", "not_a_real_type")
