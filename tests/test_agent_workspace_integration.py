from __future__ import annotations

from pathlib import Path

import secondbrain
from secondbrain.native.ai_workspace.service import AIWorkspaceService

# Real repo root (SecondBrain-Agent/), where the native module files actually
# live - module readiness is resolved against the filesystem.
REPO_ROOT = Path(secondbrain.__file__).resolve().parent.parent


def test_agent_control_registered_in_navigation(tmp_path):
    svc = AIWorkspaceService(tmp_path)
    ids = {item["id"] for item in svc.navigation()["navigation"]}
    assert "agent_control" in ids


def test_agent_control_module_ready_in_snapshot():
    svc = AIWorkspaceService(REPO_ROOT)
    modules = {m["id"]: m for m in svc.snapshot().to_dict()["modules"]}
    assert "agent_control" in modules
    assert modules["agent_control"]["status"] == "ready"
    assert modules["agent_control"]["command"] == "agent-control-center-gui"


def test_agent_control_payload_returns_overview(tmp_path):
    svc = AIWorkspaceService(tmp_path)
    payload = svc.module_payload("agent_control")
    assert payload["ok"] is True
    assert "summary" in payload
    assert payload["areas"]


def test_existing_modules_preserved():
    svc = AIWorkspaceService(REPO_ROOT)
    ids = {m["id"] for m in svc.snapshot().to_dict()["modules"]}
    for expected in {"chat", "jobs", "notifications", "agents", "memory", "dashboard", "agent_control"}:
        assert expected in ids


def test_workspace_status_ready_modules_on_repo():
    svc = AIWorkspaceService(REPO_ROOT)
    status = svc.status()
    assert status["ok"] is True
    assert status["ready_modules"] >= 1
    # agent_control counts among the ready modules
    ready = {m["id"] for m in status["modules"] if m["status"] == "ready"}
    assert "agent_control" in ready
