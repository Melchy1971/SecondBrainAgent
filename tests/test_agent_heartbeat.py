from __future__ import annotations

from datetime import datetime, timedelta, timezone

from secondbrain.agent.background_agents.models import AgentHeartbeat

from tests._bg_fakes import make_supervisor


def test_register_emits_initial_heartbeat(tmp_path):
    sup, _, _ = make_supervisor(tmp_path)
    a = sup.register("A", "import_monitor")
    hb = sup.store.get_heartbeat(a.id)
    assert hb is not None
    assert hb.state == "registered"
    assert hb.sequence == 1


def test_heartbeat_increments_sequence(tmp_path):
    sup, _, _ = make_supervisor(tmp_path)
    a = sup.register("A", "import_monitor")
    hb1 = sup.heartbeat(a.id)
    hb2 = sup.heartbeat(a.id)
    assert hb2.sequence == hb1.sequence + 1


def test_run_updates_heartbeat_to_idle(tmp_path):
    sup, _, _ = make_supervisor(tmp_path)
    a = sup.register("A", "import_monitor")
    sup.start(a.id)
    before = sup.store.get_heartbeat(a.id).sequence
    sup.run_agent(a.id)
    hb = sup.store.get_heartbeat(a.id)
    assert hb.state == "idle"                # ended successfully
    assert hb.sequence >= before + 2         # running + idle


def test_failed_run_sets_failed_heartbeat(tmp_path):
    sup, _, _ = make_supervisor(tmp_path)
    a = sup.register("A", "import_monitor", config={"force_error": True})
    sup.start(a.id)
    sup.run_agent(a.id)
    assert sup.store.get_heartbeat(a.id).state == "failed"


def test_heartbeat_staleness():
    old = AgentHeartbeat(agent_id="a", ts=(datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),
                         state="idle")
    fresh = AgentHeartbeat(agent_id="a", ts=datetime.now(timezone.utc).isoformat(), state="idle")
    assert old.is_stale(ttl_seconds=3600) is True
    assert fresh.is_stale(ttl_seconds=3600) is False


def test_status_reports_heartbeat_and_staleness(tmp_path):
    sup, _, _ = make_supervisor(tmp_path, heartbeat_ttl_seconds=3600)
    a = sup.register("A", "import_monitor")
    sup.start(a.id)
    status = sup.status(a.id)
    assert status["heartbeat"] is not None
    assert status["heartbeat_stale"] is False
    assert status["agent"]["state"] == "ACTIVE"
