from __future__ import annotations

from pathlib import Path

import pytest

from secondbrain.native.ai_workspace.service import AIWorkspaceService
from secondbrain.native.dashboard_center.service import NativeDashboardService
from secondbrain.native.task_workspace import TaskWorkspaceService

ROOT = Path(__file__).resolve().parents[1]


def test_priorities_and_dependencies_use_agent_task_store(tmp_path):
    service = TaskWorkspaceService(tmp_path)
    first = service.add_task("Vorbereitung", priority=10)["task"]
    second = service.add_task("Auswertung", priority=20, dependencies=[first["id"]])["task"]
    blocked = service.run_task(second["id"])
    assert blocked["status"] == "dependencies_pending"
    assert blocked["dependencies"] == [first["id"]]
    service.tasks_service.complete_task(first["id"])
    assert service.run_task(second["id"])["ok"] is True
    assert service.tasks()[0]["priority"] == 10


def test_missing_dependencies_are_rejected(tmp_path):
    result = TaskWorkspaceService(tmp_path).add_task("Blockiert", dependencies=["agt_missing"])
    assert result == {"ok": False, "status": "missing_dependencies", "dependencies": ["agt_missing"]}


def test_reminders_and_calendar_are_views_of_tasks(tmp_path):
    service = TaskWorkspaceService(tmp_path)
    reminder = service.add_reminder("Nachfassen", "2026-07-04T08:00:00+02:00")["task"]
    event = service.add_calendar_task("Termin", "2026-07-05T10:00:00+02:00")["task"]
    assert service.reminders()[0]["id"] == reminder["id"]
    assert service.calendar()[0]["id"] == event["id"]
    assert event["calendar_event_id"] == f"task:{event['id']}"
    with pytest.raises(ValueError, match="invalid due_at"):
        service.add_calendar_task("Fehler", "morgen")


def test_agent_job_approval_and_history_use_existing_components(tmp_path):
    service = TaskWorkspaceService(tmp_path)
    result = service.enqueue_agent_job("Index aktualisieren", priority=5, approval_required=True)
    assert result["job"]["status"] == "blocked"
    approval_id = result["task"]["approval_id"]
    decided = service.decide_approval(approval_id, True)
    assert decided["task"]["approval_status"] == "approved"
    assert service.jobs_service.get_job(result["job"]["id"]).status == "pending"
    assert service.run_task(result["task"]["id"])["ok"] is True
    assert service.jobs_service.get_job(result["job"]["id"]).status == "success"
    assert {row["source"] for row in service.history()} == {"agent", "queue"}


def test_dashboard_and_ai_workspace_integration(tmp_path):
    service = TaskWorkspaceService(tmp_path)
    service.add_reminder("Dashboard Reminder", "2026-07-04T08:00:00Z")
    dashboard = NativeDashboardService(tmp_path).snapshot().to_dict()
    tasks_card = next(card for card in dashboard["cards"] if card["id"] == "tasks")
    assert tasks_card["value"]["open"] == 1
    assert tasks_card["value"]["reminders"] == 1

    modules = {module.id: module for module in AIWorkspaceService(ROOT).snapshot().modules}
    assert modules["tasks"].status == "ready"
    assert AIWorkspaceService.VERSION == "v30.50"
