"""Sprint 44 - agent task tools acceptance tests."""
from __future__ import annotations

import pytest

from secondbrain.tasks.agent_tools import TaskAgentTools
from secondbrain.tasks.service import TaskProjectService


def _tools(tmp_path):
    return TaskAgentTools(TaskProjectService(tmp_path))


def test_agent_create_is_tagged_and_auditable(tmp_path):
    tools = _tools(tmp_path)
    res = tools.task_create(workspace_id="w1", title="Aus Doc", source_reference="doc:7", confidence=0.65)
    assert res["ok"] and res["source"] == "agent" and res["confidence"] == 0.65
    events = tools.service._read("events")  # noqa: SLF001
    created = next(e for e in events if e["event_type"] == "created")
    assert created["actor"] == "agent" and created["metadata"]["source"] == "agent"
    assert created["metadata"]["source_reference"] == "doc:7"


def test_agent_delete_requires_approval(tmp_path):
    tools = _tools(tmp_path)
    t = tools.task_create(workspace_id="w1", title="X")
    res = tools.task_delete(t["task_id"], workspace_id="w1")
    assert res["requires_approval"] is True and res["status"] == "approval_required"
    assert tools.service.get_task(t["task_id"], workspace_id="w1") is not None


def test_extract_tasks_from_text_stores_proposals_with_source(tmp_path):
    tools = _tools(tmp_path)
    text = "Hallo\nTODO: Rechnung prüfen\n- Vertrag gegenlesen\nnur Fließtext ohne Aufgabe"
    proposals = tools.extract_tasks(text, workspace_id="w1", source_reference="mail:99", confidence=0.55)
    titles = [p["title"] for p in proposals]
    assert "Rechnung prüfen" in titles and "Vertrag gegenlesen" in titles
    stored = tools.service.list_tasks(workspace_id="w1")
    assert all(t.source == "agent" and t.source_reference == "mail:99" for t in stored)
    assert all(t.status == "inbox" for t in stored)


def test_forbidden_external_actions_require_approval(tmp_path):
    tools = _tools(tmp_path)
    t = tools.task_create(workspace_id="w1", title="X")
    assert tools.create_calendar_event_from_task(t["task_id"], workspace_id="w1")["requires_approval"]
    assert tools.modify_external_task(t["task_id"], workspace_id="w1", title="y")["requires_approval"]
    assert tools.send_message(workspace_id="w1", to="a@b.c")["requires_approval"]


def test_project_tools(tmp_path):
    tools = _tools(tmp_path)
    p = tools.project_create(workspace_id="w1", title="P")
    tools.task_create(workspace_id="w1", title="a", project_id=p["project_id"])
    status = tools.project_status(p["project_id"], workspace_id="w1")
    assert status["ok"] and status["total"] == 1 and status["open"] == 1
    summary = tools.project_summary(p["project_id"], workspace_id="w1")
    assert "blocked" in summary and "overdue" in summary
