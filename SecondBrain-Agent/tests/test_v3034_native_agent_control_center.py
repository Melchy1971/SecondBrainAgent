from __future__ import annotations

from pathlib import Path

from secondbrain.native.agent_control_center import AgentControlCenter


def test_agent_control_status(tmp_path: Path) -> None:
    center = AgentControlCenter(tmp_path)
    payload = center.status()
    assert payload["ok"] is True
    assert payload["version"] == "v30.34"
    assert payload["native_primary"] is True


def test_agent_plan_classifies_document_write_task(tmp_path: Path) -> None:
    center = AgentControlCenter(tmp_path)
    payload = center.plan("Importiere Datei test.pdf")
    assert payload["ok"] is True
    assert payload["intent"] == "document"
    assert payload["requires_approval"] is True
    assert payload["steps"][2]["action"] == "approval_gate"


def test_agent_task_approval_blocks_until_confirmed(tmp_path: Path) -> None:
    center = AgentControlCenter(tmp_path)
    created = center.add_task("Repariere Index")
    task_id = created["task"]["id"]
    blocked = center.run_task(task_id)
    assert blocked["ok"] is False
    assert blocked["status"] == "approval_required"
    executed = center.run_task(task_id, confirmed=True)
    assert executed["ok"] is True
    assert executed["task"]["status"] == "done"


def test_agent_task_lifecycle_cancel(tmp_path: Path) -> None:
    center = AgentControlCenter(tmp_path)
    task = center.add_task("Prüfe Status")["task"]
    cancelled = center.cancel_task(task["id"])
    assert cancelled["ok"] is True
    assert cancelled["task"]["status"] == "cancelled"


def test_agent_logs_written(tmp_path: Path) -> None:
    center = AgentControlCenter(tmp_path)
    center.add_task("Frage nach Projektstatus")
    logs = center.logs(limit=10)
    assert logs
    assert logs[0]["event"] == "task_added"
