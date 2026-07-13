from __future__ import annotations

import json

from secondbrain.native.agent_control import AgentControlService
from secondbrain.native.agent_control.gui import (
    build_tabs,
    export_plan_explain,
    format_plan_explain_markdown,
    format_plan_explain_text,
    open_export_folder,
)
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
    row = next(p for p in plans["plans"] if p["id"] == plan_id)
    assert "maximum_risk" in row
    assert "approval_gates" in row
    assert "waiting_approval" in row
    assert "failed_steps" in row
    assert "dependencies" in row


def test_explain_plan_returns_projection(tmp_path):
    svc = AgentControlService(tmp_path)
    created = svc.create_plan("Importiere Datei test.pdf")
    plan_id = created["plan"]["id"]
    explained = svc.explain_plan(plan_id)
    assert explained["ok"] is True
    assert explained["plan_id"] == plan_id
    assert "steps" in explained


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


def test_defer_keeps_item_visible_as_open(tmp_path):
    from secondbrain.agent.safety import SafetyService

    safety = SafetyService(tmp_path)
    rec = safety.request(actor="agent", action="api.external", text="call", target="tx")

    svc = AgentControlService(tmp_path)
    deferred = svc.defer(rec["approval_id"], note="später")
    assert deferred["status"] == "deferred"

    approvals = svc.area_approvals()
    assert approvals["pending"] == 0
    assert approvals["deferred"] == 1
    assert approvals["open"] == 1


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


def test_format_plan_explain_text_contains_key_sections():
    explain = {
        "ok": True,
        "plan_id": "plan_1",
        "goal": "Importiere Datei",
        "status": "running",
        "step_count": 1,
        "maximum_risk": "high",
        "approval_gates": ["s1"],
        "risky_steps": ["s1"],
        "dependencies": {"s1": ["s0"]},
        "tool_mapping": {"s1": {"phase": "document"}},
        "steps": [
            {
                "id": "s1",
                "status": "waiting_approval",
                "risk_level": "high",
                "requires_approval": True,
                "action": "write_document",
                "tool_name": "document_write",
                "recovery_suggestion": "approval required",
            }
        ],
        "audit": [{"ts": "2026-01-01T00:00:00Z", "event": "plan_explained", "plan_id": "plan_1"}],
    }
    text = format_plan_explain_text(explain)
    assert "Plan: plan_1" in text
    assert "Approval Gates: s1" in text
    assert "Risky Steps: s1" in text
    assert "deps=s0" in text
    assert "tool_mapping=phase=document" in text
    assert "Audit (latest 10):" in text


def test_format_plan_explain_markdown_contains_sections():
    explain = {
        "ok": True,
        "plan_id": "plan_1",
        "goal": "Importiere Datei",
        "status": "running",
        "step_count": 1,
        "maximum_risk": "high",
        "approval_gates": ["s1"],
        "risky_steps": ["s1"],
        "dependencies": {"s1": ["s0"]},
        "tool_mapping": {"s1": {"phase": "document"}},
        "steps": [{"id": "s1", "status": "waiting_approval", "risk_level": "high", "requires_approval": True}],
        "audit": [{"ts": "2026-01-01T00:00:00Z", "event": "plan_explained", "plan_id": "plan_1"}],
    }
    text = format_plan_explain_markdown(explain)
    assert "# Plan Explain" in text
    assert "## Steps" in text
    assert "### s1" in text
    assert "## Audit (latest 10)" in text


def test_export_plan_explain_writes_json_and_markdown(tmp_path):
    explain = {
        "ok": True,
        "plan_id": "plan_export_1",
        "goal": "Importiere Datei",
        "status": "running",
        "step_count": 0,
        "maximum_risk": "low",
        "approval_gates": [],
        "risky_steps": [],
        "dependencies": {},
        "tool_mapping": {},
        "steps": [],
        "audit": [],
    }
    out_json = export_plan_explain(explain, tmp_path, "json")
    out_md = export_plan_explain(explain, tmp_path, "md")
    assert out_json.exists()
    assert out_md.exists()
    loaded = json.loads(out_json.read_text(encoding="utf-8"))
    assert loaded["plan_id"] == "plan_export_1"
    md = out_md.read_text(encoding="utf-8")
    assert "# Plan Explain" in md
    assert "Plan: plan_export_1" in md


def test_open_export_folder_uses_injected_opener(tmp_path):
    calls = []

    def _fake_open(path):
        calls.append(path)

    out_dir = open_export_folder(tmp_path, opener=_fake_open)
    assert out_dir.exists()
    assert out_dir.name == "exports"
    assert calls == [out_dir]
