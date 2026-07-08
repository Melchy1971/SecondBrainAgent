from __future__ import annotations

from secondbrain.native.agent_control import AgentControlService
from secondbrain.native.agent_control.gui import build_tabs
from secondbrain.native.agent_control.service import AREAS


def _populate(tmp_path):
    """Seed one of each agent artifact using the real subsystems."""
    from secondbrain.agent.goals import GoalTracker
    from secondbrain.agent.safety import SafetyService

    GoalTracker.for_project(tmp_path).create_goal("SAP Migration", milestones=[{"title": "M1"}])
    SafetyService(tmp_path).request(actor="agent", action="file.delete", text="rm", target="t1")


def test_overview_has_all_areas_and_summary(tmp_path):
    _populate(tmp_path)
    svc = AgentControlService(tmp_path)
    ov = svc.overview()
    assert ov["ok"] is True
    assert ov["areas"] == [aid for aid, _ in AREAS]
    assert ov["summary"]["goals"] == 1
    assert ov["summary"]["approvals_pending"] == 1


def test_every_area_is_collectable(tmp_path):
    _populate(tmp_path)
    svc = AgentControlService(tmp_path)
    for area_id, _ in AREAS:
        payload = svc.area(area_id)
        assert payload.get("ok") is True, area_id


def test_view_model_and_tabs(tmp_path):
    _populate(tmp_path)
    svc = AgentControlService(tmp_path)
    vm = svc.view_model()
    assert len(vm["areas"]) == 8
    tabs = build_tabs(svc)
    assert [t["id"] for t in tabs] == [aid for aid, _ in AREAS]
    assert all(isinstance(t["lines"], list) for t in tabs)


def test_unknown_area(tmp_path):
    svc = AgentControlService(tmp_path)
    assert svc.area("nope")["ok"] is False


def test_create_and_inspect_plan(tmp_path):
    svc = AgentControlService(tmp_path)
    created = svc.create_plan("Importiere Datei test.pdf")
    assert created["ok"] is True
    plan_id = created["plan"]["id"]
    inspected = svc.inspect_plan(plan_id)
    assert inspected["ok"] is True
    assert "steps" in inspected["checks"]
    # the plan now shows up in the plans area
    plans = svc.area_plans()
    assert any(p["id"] == plan_id for p in plans["plans"])


def test_approve_and_reject(tmp_path):
    from secondbrain.agent.safety import SafetyService

    safety = SafetyService(tmp_path)
    rec_a = safety.request(actor="agent", action="file.delete", text="a", target="ta")
    rec_b = safety.request(actor="agent", action="file.delete", text="b", target="tb")

    svc = AgentControlService(tmp_path)
    assert svc.approve(rec_a["approval_id"])["status"] == "approved"
    assert svc.reject(rec_b["approval_id"])["status"] == "rejected"
    # no pending approvals remain
    assert svc.area_approvals()["pending"] == 0


def test_monitor_workflow(tmp_path):
    from secondbrain.agent.workflow import WorkflowExecutor
    from secondbrain.agent.workflow_models import WorkflowStep

    ex = WorkflowExecutor(tmp_path, tool_runner=lambda step, approved: "ok")
    cp = ex.create("obj", [WorkflowStep(id="a", name="A", tool_name=None)])
    ex.run(cp.workflow_id)

    svc = AgentControlService(tmp_path)
    mon = svc.monitor_workflow(cp.workflow_id)
    assert mon["ok"] is True
    assert mon["state"] == "COMPLETED"
    assert svc.monitor_workflow("nope")["ok"] is False


def test_manage_background_agent(tmp_path):
    from secondbrain.agent.background_agents import AgentSupervisor

    sup = AgentSupervisor.for_project(tmp_path)
    agent = sup.register("Import", "import_monitor")

    svc = AgentControlService(tmp_path)
    started = svc.manage_background_agent(agent.id, "start")
    assert started["ok"] is True
    assert started["agent"]["state"] == "ACTIVE"
    ran = svc.manage_background_agent(agent.id, "run")
    assert ran["ok"] is True
    assert svc.manage_background_agent(agent.id, "bogus")["ok"] is False


def test_actions_are_logged(tmp_path):
    svc = AgentControlService(tmp_path)
    svc.create_plan("Ein Ziel")
    logs = svc.area_logs()
    assert logs["count"] >= 1
    assert any(r.get("event") == "plan_created" for r in logs["logs"])
