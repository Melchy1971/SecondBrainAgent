from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from secondbrain.native.notification_center.service import NotificationCenterService
from secondbrain.native.ai_workspace.service import AIWorkspaceService


def test_notification_status_empty(tmp_path: Path) -> None:
    svc = NotificationCenterService(tmp_path)
    status = svc.status()
    assert status["ok"] is True
    assert status["total"] == 0
    assert status["unread"] == 0


def test_notify_and_list_unread(tmp_path: Path) -> None:
    svc = NotificationCenterService(tmp_path)
    created = svc.notify("Test", "Nachricht", level="warning", category="system", action_required=True)
    assert created["ok"] is True
    listed = svc.list_items(unread_only=True)
    assert listed["count"] == 1
    item = listed["items"][0]
    assert item["title"] == "Test"
    assert item["action_required"] is True


def test_mark_read_and_snapshot(tmp_path: Path) -> None:
    svc = NotificationCenterService(tmp_path)
    item = svc.notify("Lesen", "Text")["notification"]
    assert svc.status()["unread"] == 1
    assert svc.mark_read(item["id"])["ok"] is True
    status = svc.status()
    assert status["unread"] == 0
    assert status["total"] == 1


def test_clear_keep_unread(tmp_path: Path) -> None:
    svc = NotificationCenterService(tmp_path)
    first = svc.notify("Alt", "Text")["notification"]
    svc.notify("Neu", "Text")
    svc.mark_read(first["id"])
    result = svc.clear(keep_unread=True)
    assert result["ok"] is True
    assert svc.status()["total"] == 1
    assert svc.status()["unread"] == 1


def test_workspace_navigation_contains_notifications(tmp_path: Path) -> None:
    module_dir = tmp_path / "secondbrain" / "native" / "notification_center"
    module_dir.mkdir(parents=True)
    service = AIWorkspaceService(tmp_path)
    nav = service.navigation()["navigation"]
    ids = {item["id"] for item in nav}
    assert "notifications" in ids
