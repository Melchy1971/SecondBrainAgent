"""Sprint 44 - task GUI view model acceptance tests (no technical ids)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from secondbrain.tasks.gui import KANBAN_COLUMNS, MODULES, TaskViewModel
from secondbrain.tasks.service import TaskProjectService


def _vm(tmp_path):
    return TaskViewModel(TaskProjectService(tmp_path))


def _seed(vm):
    s = vm.service
    p = s.create_project(workspace_id="w1", title="Projekt A")
    a = s.create_task(workspace_id="w1", title="Aktiv", project_id=p.project_id, status="active", priority="critical",
                      source="mail", source_reference="thread:5")
    past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    s.create_task(workspace_id="w1", title="Fällig", due_date=past, status="active")
    b_pred = s.create_task(workspace_id="w1", title="Pred")
    b = s.create_task(workspace_id="w1", title="Geblockt")
    s.add_dependency(b_pred.task_id, b.task_id, workspace_id="w1")
    return p, a, b


def test_main_items_have_no_technical_ids(tmp_path):
    vm = _vm(tmp_path)
    _seed(vm)
    for view in (vm.module_list("w1"), vm.module_today("w1"), vm.module_overdue("w1"), vm.module_blocked("w1")):
        for item in view:
            assert "task_id" not in item and "project_id" not in item
            assert "title" in item and "status" in item


def test_render_html_contains_no_ids(tmp_path):
    vm = _vm(tmp_path)
    _seed(vm)
    html = vm.render_html("w1")
    assert html.startswith("<!doctype html>")
    assert "tsk_" not in html and "prj_" not in html
    assert "AUFGABEN" in html and "Kanban" in html


def test_kanban_is_keyed_by_status(tmp_path):
    vm = _vm(tmp_path)
    _seed(vm)
    kanban = vm.module_kanban("w1")
    assert set(KANBAN_COLUMNS).issubset(kanban)
    assert any(i["title"] == "Aktiv" for i in kanban["active"])


def test_today_overdue_blocked(tmp_path):
    vm = _vm(tmp_path)
    _seed(vm)
    assert any(i["title"] == "Fällig" for i in vm.module_overdue("w1"))
    assert any(i["title"] == "Geblockt" for i in vm.module_blocked("w1"))
    assert any(i["overdue"] for i in vm.module_overdue("w1"))


def test_project_overview_has_no_ids(tmp_path):
    vm = _vm(tmp_path)
    _seed(vm)
    ov = vm.project_overview("w1")
    assert ov and all("project_id" not in p for p in ov)
    assert all("title" in p and "progress" in p for p in ov)


def test_source_reference_available_for_drilldown(tmp_path):
    vm = _vm(tmp_path)
    _seed(vm)
    active = [i for i in vm.module_list("w1") if i["title"] == "Aktiv"][0]
    assert active["source"] == "mail" and active["source_reference"] == "thread:5"


def test_detail_view_may_include_id(tmp_path):
    vm = _vm(tmp_path)
    _, a, _ = _seed(vm)
    detail = vm.detail(a.task_id, workspace_id="w1")
    assert detail["task_id"] == a.task_id


def test_modules_and_snapshot(tmp_path):
    vm = _vm(tmp_path)
    _seed(vm)
    assert MODULES == ["Aufgaben", "Projekte", "Heute", "Überfällig", "Blockiert"]
    snap = vm.snapshot("w1")
    assert set(snap["counts"]) == {"open", "overdue", "blocked"}
    assert snap["counts"]["overdue"] >= 1
