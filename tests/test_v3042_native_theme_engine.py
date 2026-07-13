from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from secondbrain.native.theme_center.service import ThemeCenterService


def test_theme_status_has_builtin_catalog(tmp_path: Path) -> None:
    svc = ThemeCenterService(tmp_path)
    status = svc.status()
    assert status["ok"] is True
    assert status["active_theme"] == "jarvis_dark"
    assert status["theme_count"] >= 4
    assert status["current"]["tokens"]["background"]


def test_theme_activate_and_reset(tmp_path: Path) -> None:
    svc = ThemeCenterService(tmp_path)
    activated = svc.activate("minimal_light")
    assert activated["ok"] is True
    assert svc.current_theme_id() == "minimal_light"
    reset = svc.reset()
    assert reset["ok"] is True
    assert svc.current_theme_id() == "jarvis_dark"


def test_theme_import_export_roundtrip(tmp_path: Path) -> None:
    svc = ThemeCenterService(tmp_path)
    exported = svc.export_theme("cyber_blue")
    assert exported["ok"] is True
    src = Path(exported["path"])
    data = json.loads(src.read_text(encoding="utf-8"))
    data["id"] = "custom_test"
    data["name"] = "Custom Test"
    custom = tmp_path / "custom.theme.json"
    custom.write_text(json.dumps(data), encoding="utf-8")
    imported = svc.import_theme(custom)
    assert imported["ok"] is True
    assert "custom_test" in svc.theme_map()


def test_theme_cli_status_from_delta(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, str(repo / "launcher.py"), "theme-status", "--project-root", str(tmp_path)],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["active_theme"] == "jarvis_dark"


def test_ai_workspace_contains_theme_navigation(tmp_path: Path) -> None:
    from secondbrain.native.ai_workspace.service import AIWorkspaceService

    (tmp_path / "secondbrain" / "native" / "theme_center").mkdir(parents=True)
    svc = AIWorkspaceService(tmp_path)
    nav = svc.navigation()["navigation"]
    assert any(item["id"] == "themes" and item["command"] == "theme-status" for item in nav)
