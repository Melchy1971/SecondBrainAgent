from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from secondbrain.native.ai_workspace.models import ApplicationState
from secondbrain.native.ai_workspace.service import AIWorkspaceService


ROOT = Path(__file__).resolve().parents[1]


def test_workspace_reports_v3045_and_real_native_modules() -> None:
    payload = AIWorkspaceService(ROOT).status()
    modules = {item["id"]: item for item in payload["modules"]}
    assert tuple(map(int, payload["version"].removeprefix("v").split("."))) >= (30, 45)
    assert modules["jobs"]["status"] == "ready"
    assert modules["chat"]["status"] == "ready"
    assert modules["documents"]["status"] == "ready"
    assert modules["memory"]["status"] == "ready"
    assert {
        "dashboard", "workspace", "chat", "documents", "memory", "agents", "voice",
        "commands", "jobs", "notifications", "settings", "themes", "updates",
    }.issubset(modules)


def test_workspace_keeps_missing_modules_disabled(tmp_path: Path) -> None:
    payload = AIWorkspaceService(tmp_path).navigation()
    assert payload["ok"] is True
    assert all(item["enabled"] is False for item in payload["navigation"])


def test_workspace_cli_status(tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "launcher.py"), "ai-workspace-status", "--project-root", str(tmp_path)],
        cwd=ROOT, text=True, capture_output=True, check=False,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert tuple(map(int, payload["version"].removeprefix("v").split("."))) >= (30, 45)
    assert payload["workspace_ready"] is False


def test_workspace_activity_roundtrip(tmp_path: Path) -> None:
    service = AIWorkspaceService(tmp_path)
    service.record_activity("integration_test", {"value": 1})
    payload = service.activity()
    assert payload["count"] == 1
    assert payload["items"][0]["event"] == "integration_test"


def test_primary_native_launcher_uses_integrated_workspace() -> None:
    source = (ROOT / "secondbrain" / "gui" / "launch.py").read_text(encoding="utf-8")
    assert "secondbrain.native.ai_workspace.gui import run_gui" in source


def test_application_state_controls_navigation() -> None:
    state = AIWorkspaceService(ROOT).application_state()
    assert isinstance(state, ApplicationState)
    state.select_module("documents")
    assert state.active_module == "documents"
    assert state.status == "ready"
    assert state.to_dict()["modules"]


def test_all_modules_have_integrated_payloads() -> None:
    service = AIWorkspaceService(ROOT)
    for module in service.snapshot().modules:
        payload = service.module_payload(module.id)
        assert payload.get("status") != "module_error", (module.id, payload)


def test_desktop_alias_uses_same_native_start(monkeypatch) -> None:
    import launcher

    calls: list[list[str]] = []
    monkeypatch.setattr(launcher, "load_env_file", lambda: None)
    monkeypatch.setattr(launcher, "gui_command", lambda argv: calls.append(argv) or 0)
    assert launcher.main(["desktop", "--project-root", str(ROOT)]) == 0
    assert calls == [["desktop", "--project-root", str(ROOT)]]
