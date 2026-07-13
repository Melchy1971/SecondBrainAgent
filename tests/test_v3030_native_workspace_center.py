from __future__ import annotations

import json
from pathlib import Path

from secondbrain.native.workspace_center import NativeWorkspaceCenter, WorkspaceActivityLog, workspace_status


def test_workspace_status_contains_expected_sections(tmp_path: Path) -> None:
    payload = workspace_status(tmp_path)
    assert payload["ok"] is True
    assert payload["version"] == "30.30"
    section_ids = {item["id"] for item in payload["sections"]}
    assert {"dashboard", "chat", "documents", "search", "memory", "tasks", "agents", "activity", "settings", "developer"}.issubset(section_ids)


def test_workspace_activity_is_jsonl_backed(tmp_path: Path) -> None:
    log = WorkspaceActivityLog(tmp_path)
    record = log.append({"kind": "test", "title": "Testaktivität", "section": "developer", "ok": True})
    assert record["title"] == "Testaktivität"
    status = log.status()
    assert status["total_activities"] == 1
    assert status["activities"][-1]["kind"] == "test"


def test_open_section_records_activity(tmp_path: Path) -> None:
    center = NativeWorkspaceCenter(tmp_path)
    result = center.open_section("documents")
    assert result["ok"] is True
    assert result["section"]["id"] == "documents"
    assert center.activity.status()["total_activities"] == 1


def test_unknown_section_is_rejected(tmp_path: Path) -> None:
    center = NativeWorkspaceCenter(tmp_path)
    result = center.open_section("does-not-exist")
    assert result["ok"] is False
    assert result["status"] == "unknown_section"


def test_workspace_model_is_json_serializable(tmp_path: Path) -> None:
    payload = NativeWorkspaceCenter(tmp_path).status()
    json.dumps(payload, ensure_ascii=False, default=str)
