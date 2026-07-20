from pathlib import Path

from secondbrain.desktop_app import DesktopAppRuntime
from secondbrain.desktop_native import app as desktop_app
from secondbrain.desktop_native.task_surface import TaskSurface, task_view_text


def test_task_surface_reports_live_counts_and_recent_items(tmp_path):
    runtime = DesktopAppRuntime(tmp_path)
    first = runtime.add_task("Erste", priority="high")
    runtime.add_task("Zweite", priority="low")
    runtime.complete_task(first["id"])

    snapshot = TaskSurface(runtime, limit=1).snapshot()

    assert snapshot["status"] == "ready"
    assert snapshot["total"] == 2
    assert snapshot["open_count"] == 1
    assert snapshot["completed_count"] == 1
    assert snapshot["visible_count"] == 1
    assert snapshot["items"][0]["title"] == "Zweite"
    assert snapshot["workspace_local"] is True


def test_task_surface_sanitizes_control_characters_and_bounds_fields(tmp_path):
    runtime = DesktopAppRuntime(tmp_path)
    runtime.add_task("Zeile 1\nZeile 2\x1b[31m" + "x" * 300)

    item = TaskSurface(runtime).snapshot()["items"][0]

    assert "\n" not in item["title"]
    assert "\x1b" not in item["title"]
    assert len(item["title"]) == 200


def test_task_surface_hides_provider_errors():
    class BrokenRuntime:
        @staticmethod
        def tasks():
            raise RuntimeError("secret local path")

    snapshot = TaskSurface(BrokenRuntime()).snapshot()

    assert snapshot["status"] == "unavailable"
    assert "secret" not in repr(snapshot)
    assert snapshot["items"] == []


def test_task_view_text_is_human_readable(tmp_path):
    runtime = DesktopAppRuntime(tmp_path)
    task = runtime.add_task("Review", priority="high")

    rendered = task_view_text(TaskSurface(runtime).snapshot())

    assert "1 offen" in rendered
    assert "[ ] Review · high" in rendered
    assert task["id"] in rendered
    assert "Aufgabe abschließen" in rendered


def test_native_shell_routes_tasks_to_surface_and_refreshes_after_writes():
    source = Path(desktop_app.__file__).read_text(encoding="utf-8")

    assert 'elif view == "Tasks":' in source
    assert "task_view_text(self.task_surface.snapshot())" in source
    assert 'action_id.startswith("tasks.")' in source
